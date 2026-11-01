"""Tools called by the LLM: order lookup and product search. No LLM needed to run them."""

import json
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORIES = pd.read_csv(DATA_DIR / "categories.csv")
CUSTOMERS = pd.read_csv(DATA_DIR / "customers.csv")
ORDERS = pd.read_csv(DATA_DIR / "orders.csv")
ORDER_ITEMS = pd.read_csv(DATA_DIR / "order_items.csv")
PRODUCTS = pd.read_csv(DATA_DIR / "products.csv")
PROMOTIONS = pd.read_csv(DATA_DIR / "promotions.csv")

ACTIVE_DISCOUNTS = dict(
    zip(
        PROMOTIONS.loc[PROMOTIONS["is_active"] == 1, "product_id"],
        PROMOTIONS.loc[PROMOTIONS["is_active"] == 1, "discount_percent"],
    )
)
CATEGORY_NAMES = dict(zip(CATEGORIES["category_id"], CATEGORIES["name"]))
CATEGORY_ENUM = [str(name) for name in CATEGORIES["name"]]

ORDER_NOT_VERIFIED = {
    "found": False,
    "message": "Não foi possível verificar o pedido com os dados informados.",
}
STATUS_LABELS = {
    "pending": "aguardando confirmação de pagamento",
    "confirmed": "confirmado, em preparação",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}
PAYMENT_LABELS = {
    "pix": "PIX",
    "debit": "cartão de débito",
    "boleto": "boleto bancário",
}

PIX_FACTOR = 0.95
MAX_RESULTS = 10
WITHDRAWAL_DAYS = 7
DEFECT_EXCHANGE_DAYS = 30
LEGAL_WARRANTY_DAYS = 90

# Descriptions of these products are unreliable, so they are left out at runtime.
# See "Assumptions and data handling" in the README.
PRODUCTS_WITHOUT_DESCRIPTION = frozenset(range(135, 145))

BRAZIL_COUNTRY_CODE = "55"
MAX_PHONE_DIGITS = 11  # area code + 9-digit number


def _normalize(text: str) -> str:
    """Lowercase and remove accents."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def _phone_digits(text: str) -> str:
    """Keep digits only and drop the Brazilian country code, if present."""
    digits = re.sub(r"\D", "", text)
    if len(digits) > MAX_PHONE_DIGITS and digits.startswith(BRAZIL_COUNTRY_CODE):
        return digits.removeprefix(BRAZIL_COUNTRY_CODE)
    return digits


def _contact_matches(customer: dict, email_or_phone: str) -> bool:
    if email_or_phone.strip().lower() == customer["email"].strip().lower():
        return True
    digits = _phone_digits(email_or_phone)
    return bool(digits) and digits == _phone_digits(customer["phone"])


def _payment_label(method: str) -> str:
    if method.startswith("credit_"):
        return f"cartão de crédito em {method.removeprefix('credit_')}"
    return PAYMENT_LABELS[method]


def _deadline(deadline: date, reference_date: date) -> dict:
    return {"date": deadline.isoformat(), "open": deadline >= reference_date}


def _order_items(order_id: int) -> list[dict]:
    rows = ORDER_ITEMS[ORDER_ITEMS["order_id"] == order_id].merge(PRODUCTS, on="product_id")
    return [
        {"name": str(row["name"]), "quantity": int(row["quantity"])}
        for row in rows.to_dict("records")
    ]


def get_order(order_id: int, email_or_phone: str, reference_date: date) -> dict:
    """Return an order's details if the contact matches the customer of that order."""
    orders = ORDERS[ORDERS["order_id"] == order_id]
    if orders.empty:
        return dict(ORDER_NOT_VERIFIED)
    order = orders.iloc[0].to_dict()

    customer = CUSTOMERS[CUSTOMERS["customer_id"] == order["customer_id"]].iloc[0].to_dict()
    if not _contact_matches(customer, email_or_phone):
        return dict(ORDER_NOT_VERIFIED)

    result = {
        "found": True,
        "customer_first_name": customer["name"].split()[0],
        "order_date": order["order_date"],
        "status": STATUS_LABELS[order["status"]],
        "items": _order_items(order_id),
        "total": round(float(order["total_brl"]), 2),
        "payment_method": _payment_label(order["payment_method"]),
    }
    if pd.notna(order["tracking_code"]):
        result["tracking_code"] = order["tracking_code"]
    if pd.notna(order["notes"]):
        result["cancellation_note"] = order["notes"]

    if pd.notna(order["estimated_delivery"]):
        result["estimated_delivery"] = order["estimated_delivery"]
        receipt = date.fromisoformat(order["estimated_delivery"])
        if order["status"] == "delivered":
            purchase = date.fromisoformat(order["order_date"])
            result["deadlines"] = {
                "withdrawal_or_preference_exchange": _deadline(
                    receipt + timedelta(days=WITHDRAWAL_DAYS), reference_date
                ),
                "defect_exchange": _deadline(
                    purchase + timedelta(days=DEFECT_EXCHANGE_DAYS), reference_date
                ),
                "legal_warranty": _deadline(
                    receipt + timedelta(days=LEGAL_WARRANTY_DAYS), reference_date
                ),
            }
        elif order["status"] == "shipped":
            result["delivery_overdue"] = receipt < reference_date

    return result


def _product_summary(row: dict) -> dict:
    product_id = int(row["product_id"])
    original_price = round(float(row["price_brl"]), 2)
    discount_percent = int(ACTIVE_DISCOUNTS.get(product_id, 0))
    final_price = round(original_price * (1 - discount_percent / 100), 2)
    # The PIX discount is not cumulative with promotions (manual, section 6.2).
    pix_price = final_price if discount_percent else round(original_price * PIX_FACTOR, 2)

    product = {
        "id": product_id,
        "name": str(row["name"]),
        "category": str(CATEGORY_NAMES[row["category_id"]]),
        "description": str(row["description"]),
        "original_price": original_price,
        "discount_percent": discount_percent,
        "final_price": final_price,
        "pix_price": pix_price,
        "stock": int(row["stock_quantity"]),
        "status": str(row["status"]),
        "specs": json.loads(row["specs"]),
    }
    if product_id in PRODUCTS_WITHOUT_DESCRIPTION:
        del product["description"]
    return product


def search_products(
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    only_available: bool = True,
) -> dict:
    """Search products, cheapest first, with active promotions applied."""
    words = _normalize(query or "").split()

    matches = []
    for row in PRODUCTS.to_dict("records"):
        if category and CATEGORY_NAMES[row["category_id"]] != category:
            continue
        name = _normalize(row["name"])
        if not all(word in name for word in words):
            continue
        if only_available and not (row["status"] == "active" and row["stock_quantity"] > 0):
            continue
        product = _product_summary(row)
        if min_price is not None and product["final_price"] < min_price:
            continue
        if max_price is not None and product["final_price"] > max_price:
            continue
        matches.append(product)

    matches.sort(key=lambda product: (product["final_price"], product["id"]))
    return {"products": matches[:MAX_RESULTS], "total_found": len(matches)}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": (
                "Consulta um pedido. Use quando o cliente perguntar sobre status, entrega, "
                "rastreamento ou prazos de troca e garantia de um pedido. Exige o número do "
                "pedido e o e-mail ou telefone do cliente; peça o que faltar antes de chamar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "Número do pedido informado pelo cliente.",
                    },
                    "email_or_phone": {
                        "type": "string",
                        "description": "E-mail ou telefone informado pelo cliente.",
                    },
                },
                "required": ["order_id", "email_or_phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Busca produtos no catálogo. Use sempre que o cliente perguntar sobre "
                "produtos, preços, promoções, estoque ou disponibilidade. Nunca informe esses "
                "dados sem consultar esta ferramenta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Palavras do nome do produto, como marca ou modelo, ex.: Takamine "
                            "GD20. Para o tipo de instrumento, use category."
                        ),
                    },
                    "category": {
                        "type": "string",
                        "enum": CATEGORY_ENUM,
                        "description": "Categoria do produto.",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Preço final mínimo em reais.",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Preço final máximo em reais.",
                    },
                    "only_available": {
                        "type": "boolean",
                        "description": (
                            "Use false para incluir produtos sem estoque, descontinuados ou "
                            "em breve, como ao buscar um item específico ou alternativas."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
]
