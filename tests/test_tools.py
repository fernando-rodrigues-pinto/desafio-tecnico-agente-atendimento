import csv
import json
from datetime import date
from pathlib import Path

import pytest

from src.tools import (
    CUSTOMERS,
    ORDERS,
    TOOLS,
    calculate_installments,
    get_order,
    search_products,
)

REFERENCE_DATE = date(2026, 3, 25)


def email_of(order_id: int) -> str:
    customer_id = ORDERS.loc[ORDERS["order_id"] == order_id, "customer_id"].iloc[0]
    return CUSTOMERS.loc[CUSTOMERS["customer_id"] == customer_id, "email"].iloc[0]


def order(order_id: int) -> dict:
    return get_order(order_id, email_of(order_id), REFERENCE_DATE)


def product(query: str) -> dict:
    results = search_products(query=query, only_available=False)
    assert results["total_found"] == 1
    return results["products"][0]


def available_ids(**filters) -> list[int]:
    return [item["id"] for item in search_products(**filters)["products"]]


# get_order


def test_order_found_by_email_with_different_case():
    result = get_order(1, "  PEDRO.Oliveira@JMAIL.com ", REFERENCE_DATE)
    assert result["found"] is True
    assert result["customer_first_name"] == "Pedro"
    assert result["order_date"] == "2025-10-15"
    assert result["status"] == "entregue"
    assert result["payment_method"] == "PIX"
    assert result["items"] == [{"name": "Martin D-28 Dreadnought Natural", "quantity": 1}]
    assert result["tracking_code"] == "BRAB1234567BR"


@pytest.mark.parametrize("phone", ["(67) 98432-1098", "67 98432 1098", "67984321098"])
def test_order_found_by_phone_with_punctuation_or_spaces(phone):
    assert get_order(1, phone, REFERENCE_DATE)["found"] is True


@pytest.mark.parametrize("phone", ["+55 (67) 98432-1098", "5567984321098"])
def test_order_found_by_phone_with_country_code(phone):
    assert get_order(1, phone, REFERENCE_DATE)["found"] is True


@pytest.mark.parametrize("phone", ["98432-1098", "+55 98432-1098"])
def test_phone_without_area_code_is_rejected(phone):
    assert get_order(1, phone, REFERENCE_DATE)["found"] is False


def test_wrong_contact_and_missing_order_return_identical_results():
    wrong_contact = get_order(1, "other@jmail.com", REFERENCE_DATE)
    missing_order = get_order(9999, "pedro.oliveira@jmail.com", REFERENCE_DATE)
    assert wrong_contact == missing_order
    assert wrong_contact["found"] is False
    assert set(wrong_contact) == {"found", "message"}


def test_contact_of_another_customer_is_rejected():
    assert get_order(1, email_of(2), REFERENCE_DATE)["found"] is False


def test_empty_contact_is_rejected():
    assert get_order(1, "", REFERENCE_DATE)["found"] is False


def test_order_7_only_legal_warranty_is_open():
    result = order(7)
    assert result["delivery_forecast"] == "2026-02-17"
    assert "estimated_delivery" not in result
    deadlines = result["deadlines"]
    assert deadlines["withdrawal_or_preference_exchange"] == {"date": "2026-02-24", "open": False}
    assert deadlines["defect_exchange"] == {"date": "2026-03-05", "open": False}
    assert deadlines["legal_warranty"] == {"date": "2026-05-18", "open": True}


def test_deadline_is_open_on_its_last_day():
    result = get_order(7, email_of(7), date(2026, 5, 18))
    assert result["deadlines"]["legal_warranty"]["open"] is True


def test_order_8_shipped_is_overdue():
    result = order(8)
    assert result["status"] == "enviado"
    assert result["delivery_forecast"] == "2026-02-28"
    assert result["delivery_overdue"] is True
    assert "deadlines" not in result


def test_shipped_order_is_not_overdue_on_the_estimated_date():
    assert get_order(8, email_of(8), date(2026, 2, 28))["delivery_overdue"] is False


def test_cancelled_order_includes_its_note():
    result = order(17)
    assert result["status"] == "cancelado"
    assert result["cancellation_note"] == "Pedido cancelado pelo cliente antes do processamento"


def test_pending_order_omits_empty_fields():
    result = order(14)
    assert result["status"] == "aguardando confirmação de pagamento"
    for field in ("tracking_code", "delivery_forecast", "cancellation_note", "deadlines"):
        assert field not in result


def test_credit_payment_method_is_translated():
    assert order(2)["payment_method"] == "cartão de crédito em 6x"


@pytest.mark.parametrize("order_id", [15, 20])
def test_orders_with_two_items(order_id):
    assert len(order(order_id)["items"]) == 2


def test_order_3_returns_recorded_total_not_sum_of_items():
    result = order(3)
    assert result["items"] == [{"name": "Kala KA-ABP-CTG Barítono Cedar", "quantity": 2}]
    assert result["total"] == 3450.0  # 2 x 1749.00 would be 3498.00


# search_products


def test_category_returns_only_that_category():
    results = search_products(category="Violões")
    assert results["total_found"] == 33  # 35 violões minus products 96 and 113
    assert all(item["category"] == "Violões" for item in results["products"])


def test_category_uses_exact_equality():
    assert search_products(category="violoes") == {"products": [], "total_found": 0}


def test_query_without_accent_finds_acoustic_drums():
    assert available_ids(query="acustica") == [139, 140, 141]


def test_query_does_not_match_category_name():
    assert available_ids(query="ukulele") == []


def test_query_finds_product_by_name():
    assert product("Takamine GD20")["id"] == 95


def test_all_query_words_must_match():
    assert available_ids(query="Takamine piano") == []


def test_category_with_max_price_is_available_and_sorted():
    results = search_products(category="Violões", max_price=1000)["products"]
    prices = [item["final_price"] for item in results]
    assert results
    assert all(item["status"] == "active" and item["stock"] > 0 for item in results)
    assert all(price <= 1000 for price in prices)
    assert prices == sorted(prices)


def test_price_filters_use_final_price():
    # Product 121 costs 549.00 and 439.20 with its promotion.
    assert 121 in available_ids(query="Ohana CK-20", max_price=450)
    assert 121 not in available_ids(query="Ohana CK-20", min_price=500)


@pytest.mark.parametrize(
    "query, product_id, original, discount, final",
    [
        ("Crafter HT-100", 90, 2399.0, 18, 1967.18),
        ("Taylor 110e", 94, 5999.0, 8, 5519.08),
        ("Ohana CK-20", 121, 549.0, 20, 439.2),
        ("Kalani KAL-700T", 127, 359.0, 10, 323.1),
    ],
)
def test_active_promotions(query, product_id, original, discount, final):
    item = product(query)
    assert item["id"] == product_id
    assert item["original_price"] == original
    assert item["discount_percent"] == discount
    assert item["final_price"] == final
    assert item["pix_price"] == final


def test_inactive_promotion_is_ignored():
    assert product("Martin D-28 Dreadnought")["discount_percent"] == 0  # product 93


def test_product_without_promotion_gets_pix_discount():
    item = product("Yamaha C40")
    assert item["discount_percent"] == 0
    assert item["final_price"] == item["original_price"] == 599.9
    assert item["pix_price"] == round(599.9 * 0.95, 2)


@pytest.mark.parametrize(
    "query, product_id",
    [("Giannini GF-3D", 96), ("Shelby SN-7C", 113), ("Kala KA-ABP-CTG", 130)],
)
def test_unavailable_products_only_with_flag(query, product_id):
    assert available_ids(query=query) == []
    assert available_ids(query=query, only_available=False) == [product_id]


def test_status_is_returned_for_unavailable_products():
    assert product("Giannini GF-3D")["stock"] == 0
    assert product("Shelby SN-7C")["status"] == "discontinued"
    assert product("Kala KA-ABP-CTG")["status"] == "coming_soon"


def test_products_135_to_144_have_no_description():
    assert "description" not in product("Music Man Bass 1X")
    assert "description" in product("Yamaha C40")


def test_specs_are_parsed():
    assert product("Yamaha C40")["specs"]["top"] == "Spruce"


@pytest.mark.parametrize(
    "category",
    ["Instrumentos de Sopro (Madeiras)", "Instrumentos de Sopro (Metais)", "Cordas Orquestrais"],
)
def test_category_without_products_returns_empty_list(category):
    assert search_products(category=category) == {"products": [], "total_found": 0}


def test_results_are_limited_to_10_with_total_found():
    results = search_products(only_available=False)
    assert len(results["products"]) == 10
    assert results["total_found"] == 65


# Installments


@pytest.mark.parametrize(
    "price, count, value",
    [
        (40.0, 1, 40.0),  # below R$ 50,00
        (99.9, 1, 99.9),  # 2x would be 49.95
        (100.0, 2, 50.0),
        (149.9, 2, 74.95),
        (150.0, 3, 50.0),
        (319.9, 3, 106.63),
        (320.0, 4, 80.0),
        (479.9, 5, 95.98),
        (480.0, 6, 80.0),
        (699.9, 6, 116.65),
        (700.0, 7, 100.0),
        (1199.9, 11, 109.08),
        (1200.0, 12, 100.0),
    ],
)
def test_installment_tiers(price, count, value):
    assert calculate_installments(price) == {"max_installments": count, "installment_value": value}


def test_installments_of_a_real_product_match_the_csv():
    path = Path(__file__).resolve().parent.parent / "data" / "products.csv"
    with path.open(encoding="utf-8") as file:
        price = next(float(row["price_brl"]) for row in csv.DictReader(file) if row["product_id"] == "95")
    item = product("Takamine GD20")
    assert price == 2199.0
    assert item["max_installments"] == 12
    assert item["installment_value"] == round(price / 12, 2) == 183.25


def test_installments_use_the_promotional_price():
    item = product("Ohana CK-20")  # 549.00 with 20% off -> 439.20
    assert item["max_installments"] == 5
    assert item["installment_value"] == 87.84


# Output format and schemas


def test_results_are_json_serializable():
    json.dumps(order(1))
    json.dumps(search_products(only_available=False))


def test_tool_schemas_match_functions_and_hide_reference_date():
    schemas = {tool["function"]["name"]: tool["function"] for tool in TOOLS}
    assert set(schemas) == {"get_order", "search_products"}
    get_order_params = schemas["get_order"]["parameters"]["properties"]
    assert set(get_order_params) == {"order_id", "email_or_phone"}


def test_category_enum_has_only_the_6_categories_with_products():
    data = Path(__file__).resolve().parent.parent / "data"
    with (data / "products.csv").open(encoding="utf-8") as file:
        used_ids = {row["category_id"] for row in csv.DictReader(file)}
    with (data / "categories.csv").open(encoding="utf-8") as file:
        expected = [row["name"] for row in csv.DictReader(file) if row["category_id"] in used_ids]
    search = next(tool for tool in TOOLS if tool["function"]["name"] == "search_products")
    enum = search["function"]["parameters"]["properties"]["category"]["enum"]
    assert len(expected) == 6
    assert enum == expected
    assert "Cordas Orquestrais" not in enum
