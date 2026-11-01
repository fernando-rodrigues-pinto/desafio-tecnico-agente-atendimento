# desafio-tecnico-agente-atendimento

LLM customer service agent for a fictional music store, built in Python with native function calling.

> **Status:** work in progress. Sections marked _TBD_ will be completed as the project evolves.

## Overview

"Empório da Música" is a fictional musical instrument store in Campo Grande/MS, Brazil. This project prototypes a text-based agent that helps the store's staff by answering recurring customer questions: opening hours, order status, product prices and availability, and store policies.

Documentation is in English; the agent, data and store policies are in Portuguese, as the target customers are Brazilian.

## Architecture (one sentence)

**Facts that change come from tools; stable rules live in the prompt.**

- **Operational data** (`data/*.csv`) is accessed through two Python tools called by the LLM via native function calling: product search and order lookup (with identity verification).
- **Store policies** (`data/políticas_da_loja.pdf`, ~3k tokens) are placed in full in the system prompt, with no retrieval.
- **Interface:** simple CLI.

## Repository structure

```
.env.example      environment variables template (copy to .env)
requirements.txt  Python dependencies
data/             original challenge files (never modified)
data/policies.md  policy manual in Markdown (from the PDF, with the decisions below applied)
docs/             project documentation
```

_More folders will be added as the project evolves._

## How to run

_TBD_

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
- Orders below the installment minimums (orders 9, 16 and 18): chose to report them as recorded and, if a customer raises one, state the current rule, say the reason is unknown and offer to escalate, over saying the rules may have changed, because all three orders postdate manual version 2.1 (June 2025), so that explanation has no support in the data. Limitation: the customer gets no reason for the difference, and some cases will need staff follow-up.

## Known limitations and future work

_TBD_

## Use of AI coding assistants

_TBD_