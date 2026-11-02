# desafio-tecnico-agente-atendimento

LLM customer service agent for a fictional music store, built in Python with native function calling.

## Overview

"Empório da Música" is a fictional musical instrument store in Campo Grande/MS, Brazil. This project prototypes a text-based agent that helps the store's staff by answering recurring customer questions: opening hours, order status, product prices and availability, and store policies.

Documentation is in English; the agent, data and store policies are in Portuguese, as the target customers are Brazilian.

## Architecture (one sentence)

**Facts that change come from tools; stable rules live in the prompt.**

- **Operational data** (`data/*.csv`) is accessed through two Python tools called by the LLM via native function calling: product search and order lookup (with identity verification).
- **Store policies** (`data/policies.md`, the Markdown version of `data/policies.pdf` with my decisions applied, ~3k tokens) are placed in full in the system prompt, with no retrieval.
- **Interface:** simple CLI.

## Repository structure

```
.env.example      environment variables template (copy to .env)
requirements.txt  Python dependencies
data/             original challenge files (never modified)
data/policies.md  policy manual in Markdown (from the PDF, with the decisions below applied)
docs/             project documentation (AI-assisted workflow log)
examples/         example conversations generated from real runs
scripts/          script that generates the example conversations
src/tools.py      the two tools (search_products, get_order) and their schemas
src/agent.py      system prompt, store hours and the tool-calling loop
src/main.py       CLI
tests/            pytest tests for the tools and the agent's pure functions (no LLM)
```

## How to run

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then set LLM_API_KEY
```

The default provider is DeepSeek (`deepseek-flash`); get an API key at https://platform.deepseek.com. Any OpenAI-compatible API works by changing the three `LLM_*` variables in `.env`. For example, Gemini:

```
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-3.5-flash-lite   # or gemini-3.6-flash
```

```bash
python -m src.main           # start the chat ("sair" exits)
python -m src.main --debug   # also print each tool call
python -m pytest             # run the tests (no API key needed)
```

## Example conversations

The files in `examples/` come from single real runs of `scripts/generate_examples.py` with `deepseek-flash`, with no manual editing of the dialogue. When an answer breaks a rule, the file keeps it as generated and describes the problem in a "Known issue" note at the top.

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

- Approach: I chose native function calling in a simple loop (`src/agent.py`) over agent frameworks (LangChain/LangGraph) because one loop and two tools need no orchestration layer, and fewer abstractions make the agent easy to explain and debug. Limitation: features a framework provides (persistence, tracing) would have to be written by hand.
- Policies: I chose to put the full manual (~3k tokens) in the system prompt over retrieval (BM25/embeddings) because the document is small and retrieval could return the wrong section. Limitation: this would change with a bigger manual or many documents.
- Data: I chose two tools over pandas DataFrames loaded in memory over the alternatives below, because the tools return exact, filtered data and only the data of the verified customer. Limitation: the CSVs are read once at startup, so changes need a restart. Rejected:
  - all CSVs in the prompt: would fit, but exposes every customer's data to any user, leaves filters and math to the LLM and doesn't scale;
  - RAG over the CSVs: bad for numeric filters and exact prices;
  - a text-to-SQL agent: less predictable, risks exposing data and is unnecessary for 2 query types.
- Only two tools: I chose to return alternatives, installments and deadlines as fields computed inside `search_products` and `get_order` over adding new tools because each new tool is one more decision for the LLM. Limitation: tool results are larger.
- Arithmetic and dates: I chose to compute prices, PIX, installments, deadlines and store hours in Python over leaving them to the LLM because Python is exact and testable. Limitation: every new kind of calculation needs code.
- Identity verification: I chose to require the order number plus the email or phone of that order's customer, with the same generic message for "not found" and "wrong data", over a lookup by contact alone, so the agent never reveals whether an order exists. Limitation: the customer is not told which piece of data is wrong.
- Reference date/time: I chose a configurable `REFERENCE_DATETIME` over the system clock so deadlines and store hours are reproducible with the challenge data. Limitation: a real deployment would use the system clock.
- Conversation history: I chose to keep it in memory during the session over persisting it because a CLI prototype doesn't need persistence. Limitation: the history is lost when the CLI exits and is never trimmed in long sessions.
- Interface: I chose a CLI with a `--debug` mode that prints tool calls over a web UI or API because it is the simplest way to use the agent and see what it does. Limitation: no web or API access.
- LLM provider: I chose `deepseek-flash` (DeepSeek, with thinking mode at its default) as the default model and the model of the final examples over Gemini (`gemini-3.6-flash`, then `gemini-3.5-flash-lite`), which was used during development and dropped because its free-tier quotas blocked testing. The design stays provider-agnostic: the agent only uses the OpenAI-compatible API with native function calling, and the provider is chosen in `.env`, with no provider-specific parameters in the code. Limitation: fields that a provider requires back after a tool call (Gemini's thought signatures, DeepSeek's `reasoning_content`) are kept by appending the assistant message as returned; another provider could need something else.
- Alternatives for unavailable products: I chose to compute them in `search_products` (up to 3 available products of the same category, priced within ±30% of the requested product, closest price first) over letting the LLM search for them, because `gemini-3.5-flash-lite` invented products twice exactly when it had to decide to search for alternatives. Whatever can be deterministic should not depend on the LLM. Limitation: the rule only looks at category and price, so a 7-string nylon guitar can get 6-string steel alternatives.

## Assumptions and data handling

`data/policies.md` is the manual from `data/policies.pdf` with the policy decisions below applied; the PDF stays as the unchanged source.

- WhatsApp number: I chose (67) 3321-4500 (section 7) over (67) 3341-4444 (cover, section 1.2) because section 7 is the section that describes the channel. Limitation: the PDF doesn't say which is correct, and 3341-4444 is dropped from `data/policies.md`, so no voice line is listed.
- Email address: I chose the address without the accent over the accented one in section 1.2 because accented domains are rare and error-prone. Limitation: the domain is fictional, so this can't be verified.
- Installments: I chose the tiered rules in section 3.1 (minimum installment R$ 50,00 up to 3x, R$ 80,00 for 4x–6x, R$ 100,00 for 7x–12x) over the flat R$ 100,00 in the section 3 table because 3.1 is more specific, and read "exceto abaixo de R$ 50,00" as a R$ 50,00 minimum. Limitation: that reading is an interpretation, and the original phrase could also mean a minimum purchase value.
- Partner stores: I chose an explicit rule not to name any store over keeping "Sugerir lojas parceiras" because no partners are listed and the LLM could invent one. Limitation: customers asking for accessories get no alternative, and real partners would need a list added.
- Catalog claims: I chose to remove "mais de 300 instrumentos" and the wind and orchestral strings mentions over stating real counts because `data/products.csv` has 65 products in 6 categories, and a count in the prompt would go stale. Limitation: sections 4.4 and 8.3 still mention wind instruments, and `data/categories.csv` keeps 3 empty categories (they are left out of the `category` enum of `search_products`, so the LLM is not led to offer them).
- Defects after 30 days: I chose to layer the 30-day exchange, the legal warranty and the manufacturer warranty over keeping "acionar a garantia diretamente com o fabricante" because section 8.1 gives 90 days from receipt and the store follows the CDC. Limitation: the manual doesn't describe the process for days 31–90, so the agent can state the warranty applies but not the steps.
- Free shipping threshold: I chose free shipping from R$ 500,00 over charging the fee at exactly that value because neither rule covered it and the customer-favorable reading is safer. Limitation: this is an interpretation, and the manual doesn't say whether the threshold applies before or after discounts.
- Preference exchanges: I chose 7 calendar days from receipt over counting from purchase because section 4.1, the other 7-day rule, counts that way and customers can't judge a product before receiving it. Limitation: this is an interpretation, and `data/orders.csv` has no actual delivery date, so deadlines can only be estimated.
- Promotions data: I chose to only document discounts in `data/promotions.csv` that fall outside section 6.1, and duplicate rows for products 93, 96 and 99, over validating them in code because all of them are inactive and `search_products` applies only `is_active=1`. Limitation: the file has no dates, so `is_active` is the only validity signal, and the agent can't say when a promotion ended.
- Orders below the installment minimums (orders 9, 16 and 18): I chose to report them as recorded and, if a customer raises one, state the current rule, say the reason is unknown and direct the customer to WhatsApp, over saying the rules may have changed, because all three orders postdate manual version 2.1 (June 2025), so that explanation has no support in the data. Limitation: the customer gets no reason for the difference, and some cases will need staff follow-up.
- Descriptions of products 135-144: I chose, deliberately, to exclude the unreliable descriptions of these products (all basses, drums and keyboards; 7 of the 10 contradict the product name, and all 10 come from the same batch, so they are treated together) at runtime in `search_products` over editing them in the CSV or deactivating the products because, following the initial decision not to alter any of the challenge's original data, editing them would mean inventing content, and deactivating the products would empty 3 categories. Limitation: the ID list is hardcoded and must be reviewed if the data changes.
- Phone verification: I chose to accept numbers with or without +55 but require the area code over an exact digit match because customers often type the country code. Limitation: numbers without area code are rejected.
- Complaints (section 7.3): I chose to have the agent direct the customer to WhatsApp over registering the complaint and forwarding it to the person in charge, as the manual says, because the agent has no way to register or forward messages. Limitation: complaints depend on the customer contacting the store.
- Installment calculation: I chose to compute the maximum number of interest-free installments and their value in Python, on the final price (with any active promotion, without the PIX discount), taking the highest count whose installment meets the section 3.1 minimum (R$ 50,00 up to 3x, R$ 80,00 for 4x–6x, R$ 100,00 for 7x–12x; 1x below R$ 50,00), over letting the LLM do the math because arithmetic stays out of the LLM. Limitation: each installment is rounded to the cent, so the installments can add up to a few cents more or less than the price.

### Data findings

Documented, not fixed in code:

- Order totals differ from the sum of their items in orders 3 (R$ 3.450,00 vs R$ 3.498,00) and 20 (R$ 1.400,00 vs R$ 1.488,00); the agent reports the recorded total.
- Customers 11 and 43 share the same email, so that email passes verification for customer 11's order 10 (customer 43 has no orders). This is a privacy limitation; customer deduplication is future work.
- Product 130 is `coming_soon` but appears in orders 3 and 14; product 136 is `discontinued` with 13 units in stock; product 96 is `active` with no stock (and appears in order 4).
- The 5 PIX orders (1, 5, 10, 13 and 17) were charged the full item price, without the 5% PIX discount.
- There is no sales channel in the data, so all purchases are treated as online: `get_order` returns the withdrawal deadline for every delivered order.
- There is no actual delivery date, so `estimated_delivery` is used as the receipt date for deadlines (and returned as `delivery_forecast`).

## Known limitations and future work

- Holidays: the store is closed on holidays (manual, section 2), but there is no holiday data, so the open/closed status injected into the prompt only uses weekdays and hours.
- Rate limits: the free tier of the Gemini API limits requests per minute and per day (the current values are shown only in Google AI Studio), which is why Gemini is no longer the default. If it is chosen in `.env`, a fast conversation can hit the limit, since each question that uses a tool takes 2 requests, and get the friendly error message.
- Tone details: the model may add small details that are not in the manual or in the product data to keep the tone friendly, e.g. inviting the customer "for a coffee" at the store, or calling the Yamaha C70's tone "bem mais encorpado" in `examples/01_product_catalog.md` while its description says "timbre equilibrado".
- Prompt-only rules: in my test runs with `gemini-3.5-flash-lite` (4 example generations with 20 conversations, plus the step 4 behavior tests: 14 scenarios and a re-run of 4), rules enforced in code (alternatives for unavailable products, installments, order deadlines, the category list) never failed, while prompt-only rules were followed inconsistently (the delivery forecast presented as the delivery date, offers to calculate shipping, and invented products before the alternatives moved into code). The final set, generated once with `deepseek-flash` (5 conversations), has no rule violations, but that is a single run, and prompt-only rules remain the weakest part of the design.
- Third-party LLM provider: customer and order data returned by the tools is sent to the LLM provider. This is acceptable here because the data is fictional; real data would need a provider and contract that allow it.

With more time:

- conversation persistence across sessions;
- a real handoff to a human (ticket or queue) instead of pointing to WhatsApp;
- a web UI or API;
- an automated evaluation suite for agent behavior (scripted scenarios with checks on the answers);
- customer deduplication;
- a holiday calendar for the store hours.

## Use of AI coding assistants

> **DRAFT** — written by the AI from `docs/ai-workflow.md` for me to review; I will rewrite it in my own words.

- **Tools:** Claude (claude.ai) as a technical mentor for planning, specifications and review; Claude Code for implementation, tests and running the agent.
- **Workflow:** I planned and specified each step in the chat, handed Claude Code a detailed prompt, reviewed the output, and accepted or corrected it, with one step per commit/PR.
- **Where I rejected or changed a suggestion:**
  - The AI's fix for searching "violao" (matching category names plus a "violao" alias) was replaced by a `category` enum with exact matching.
  - When the agent answered a regret question with only the relevant deadlines, the AI proposed making `get_order` return a ready summary of all three; I rejected it because the test criterion was wrong, and relaxed the rule instead.
  - I first kept the 3 empty categories in the enum; after the model claimed the store sells wind instruments, I removed them.
  - When the Lite model invented products while looking for alternatives, I moved that decision into code instead of switching models.
  - I switched the provider from Gemini to DeepSeek when free-tier quotas kept blocking test runs.
- **Rule kept throughout:** example conversations come only from real runs of the script, never written or edited by hand; answers that broke a rule were kept and documented, not re-run until a clean one appeared.
- The full step-by-step log is in [`docs/ai-workflow.md`](docs/ai-workflow.md).