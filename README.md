# desafio-tecnico-agente-atendimento

LLM customer service agent for a fictional music store, built in Python with native function calling.

> **Status:** work in progress. Sections marked _TBD_ will be completed as the project evolves.

## Overview

"Empório da Música" is a fictional musical instrument store in Campo Grande/MS, Brazil. This project prototypes a text-based agent that helps the store's staff by answering recurring customer questions: opening hours, order status, product prices and availability, and store policies.

Documentation is in English; the agent, data and store policies are in Portuguese, as the target customers are Brazilian.

## Architecture (one sentence)

**Facts that change come from tools; stable rules live in the prompt.**

- **Operational data** (`data/*.csv`) is accessed through two Python tools called by the LLM via native function calling: product search and order lookup (with identity verification).
- **Store policies** (`data/policies.pdf`, ~3k tokens) are placed in full in the system prompt, with no retrieval.
- **Interface:** simple CLI.

## Repository structure

```
.env.example      environment variables template (copy to .env)
requirements.txt  Python dependencies
data/             original challenge files (never modified)
data/policies.md  policy manual in Markdown (from the PDF, with the decisions below applied)
docs/             project documentation
examples/         example conversations generated from real runs
scripts/          script that generates the example conversations
```

_More folders will be added as the project evolves._

## How to run

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set LLM_API_KEY
```

```bash
python -m src.main           # start the chat ("sair" exits)
python -m src.main --debug   # also print each tool call
python -m pytest             # run the tools tests (no API key needed)
```

## Example conversations

The files in `examples/` come from single real runs of `scripts/generate_examples.py` with `gemini-3.5-flash-lite`, with no manual editing of the dialogue. When an answer breaks a rule, the file keeps it as generated and describes the problem in a "Known issue" note at the top.

- `01_product_catalog.md`: catalog search with a price filter, follow-up questions using the conversation memory, and installments.
- `02_price_and_availability.md`: price of a product, an out-of-stock product and a discontinued product.
- `03_store_information.md`: address, opening hours and shipping, answered from the policy manual without tools.
- `04_return_request.md`: identity check, order data and the return policy, with deadlines computed in Python.
- `05_out_of_scope_and_privacy.md`: out-of-scope requests, an instruction override attempt and two failed identity checks.

To regenerate them (requires `.env`; each run calls the LLM, so the answers will differ):

```bash
python -m scripts.generate_examples      # all conversations
python -m scripts.generate_examples 3    # only conversation 3
```

## Technical decisions

_TBD_

## Assumptions and data handling

`data/policies.md` is the manual from `data/policies.pdf` with the policy decisions below applied; the PDF stays as the unchanged source.

- WhatsApp number: chose (67) 3321-4500 (section 7) over (67) 3341-4444 (cover, section 1.2) because section 7 is the section that describes the channel. Limitation: the PDF doesn't say which is correct, and 3341-4444 is dropped from `data/policies.md`, so no voice line is listed.
- Email address: chose the address without the accent over the accented one in section 1.2 because accented domains are rare and error-prone. Limitation: the domain is fictional, so this can't be verified.
- Installments: chose the tiered rules in section 3.1 (minimum installment R$ 50,00 up to 3x, R$ 80,00 for 4x–6x, R$ 100,00 for 7x–12x) over the flat R$ 100,00 in the section 3 table because 3.1 is more specific, and read "exceto abaixo de R$ 50,00" as a R$ 50,00 minimum. Limitation: that reading is an interpretation, and the original phrase could also mean a minimum purchase value.
- Partner stores: chose an explicit rule not to name any store over keeping "Sugerir lojas parceiras" because no partners are listed and the LLM could invent one. Limitation: customers asking for accessories get no alternative, and real partners would need a list added.
- Catalog claims: chose to remove "mais de 300 instrumentos" and the wind and orchestral strings mentions over stating real counts because `data/products.csv` has 65 products in 6 categories, and a count in the prompt would go stale. Limitation: sections 4.4 and 8.3 still mention wind instruments, and `data/categories.csv` keeps 3 empty categories.
- Defects after 30 days: chose to layer the 30-day exchange, the legal warranty and the manufacturer warranty over keeping "acionar a garantia diretamente com o fabricante" because section 8.1 gives 90 days from receipt and the store follows the CDC. Limitation: the manual doesn't describe the process for days 31–90, so the agent can state the warranty applies but not the steps.
- Free shipping threshold: chose free shipping from R$ 500,00 over charging the fee at exactly that value because neither rule covered it and the customer-favorable reading is safer. Limitation: this is an interpretation, and the manual doesn't say whether the threshold applies before or after discounts.
- Preference exchanges: chose 7 calendar days from receipt over counting from purchase because section 4.1, the other 7-day rule, counts that way and customers can't judge a product before receiving it. Limitation: this is an interpretation, and `data/orders.csv` has no actual delivery date, so deadlines can only be estimated.
- Promotions data: chose to only document discounts in `data/promotions.csv` that fall outside section 6.1, and duplicate rows for products 93, 96 and 99, over validating them in code because all of them are inactive and `search_products` applies only `is_active=1`. Limitation: the file has no dates, so `is_active` is the only validity signal, and the agent can't say when a promotion ended.
- Orders below the installment minimums (orders 9, 16 and 18): chose to report them as recorded and, if a customer raises one, state the current rule, say the reason is unknown and direct the customer to WhatsApp, over saying the rules may have changed, because all three orders postdate manual version 2.1 (June 2025), so that explanation has no support in the data. Limitation: the customer gets no reason for the difference, and some cases will need staff follow-up.
- Descriptions of products 135-144: chose, deliberately, to exclude the unreliable descriptions of these products (all basses, drums and keyboards; 7 of the 10 contradict the product name, and all 10 come from the same batch, so they are treated together) at runtime in `search_products` over editing them in the CSV or deactivating the products because, following the initial decision not to alter any of the challenge's original data, editing them would mean inventing content, and deactivating the products would empty 3 categories. Limitation: the ID list is hardcoded and must be reviewed if the data changes.
- Phone verification: chose to accept numbers with or without +55 but require the area code over an exact digit match because customers often type the country code. Limitation: numbers without area code are rejected.
- Complaints (section 7.3): chose to have the agent direct the customer to WhatsApp over registering the complaint and forwarding it to the person in charge, as the manual says, because the agent has no way to register or forward messages. Limitation: complaints depend on the customer contacting the store.
- Installment calculation: chose to compute the maximum number of interest-free installments and their value in Python, on the final price (with any active promotion, without the PIX discount), taking the highest count whose installment meets the section 3.1 minimum (R$ 50,00 up to 3x, R$ 80,00 for 4x–6x, R$ 100,00 for 7x–12x; 1x below R$ 50,00), over letting the LLM do the math because arithmetic stays out of the LLM. Limitation: each installment is rounded to the cent, so the installments can add up to a few cents more or less than the price.

## Known limitations and future work

- Holidays: the store is closed on holidays (manual, section 2), but there is no holiday data, so the open/closed status injected into the prompt only uses weekdays and hours.
- Free-tier rate limits: the free tier of the Gemini API limits requests per minute and per day (the current values are shown only in Google AI Studio), and each question that uses a tool takes 2 requests, so a fast conversation can hit the limit and get the friendly error message.
- Tone details: the model may add small details that are not in the manual to keep the tone friendly (e.g. inviting the customer "for a coffee" at the store).
- Rule violations in the examples: in the final run, `gemini-3.5-flash-lite` broke rules in 3 of the 5 example conversations (a wrong minimum installment in 01, products that are not in the catalog in 02, and wind instruments in 05). They are kept as generated, with a "Known issue" note, instead of re-running until a clean answer appears.

## Use of AI coding assistants

_TBD_