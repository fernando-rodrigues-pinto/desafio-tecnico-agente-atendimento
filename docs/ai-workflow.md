# AI-assisted workflow log

Log of how AI coding assistants were used in this project: what was asked, what was accepted and what was adjusted. 

**Tool:** Claude (claude.ai, Claude Opus 5.5), used as pair programmer. All generated code and text is reviewed.

## Step 0: Initial setup

- **Asked:** a repository description and the initial structure (README, AGENTS.md, .gitignore).
- **Accepted:** documentation and code identifiers in English; only customer-facing content (prompt, replies) in Portuguese. Tools renamed to `search_products` and `get_order`.
- **Adjusted:** minor details in text.

## Step 1: Setup and store policy manual

- **Asked:** `requirements.txt`, `.env.example` and a Markdown version of the policy PDF. I listed the known manual inconsistencies and asked to review each one, one at a time, so I could decide it.
- **Accepted:** the dependency versions; the extra inconsistencies the AI found beyond my list (f to j); and its recommended option for the email, installments, partner stores, catalog claims, defects after 30 days, free shipping threshold, preference exchanges and promotions data.
- **Adjusted:** I rejected the recommended WhatsApp number and chose the one in section 7. I first asked for a verbatim manual, then changed my mind so that `data/policies.md` reflects my decisions, with each change listed in the README. For orders below the installment minimums, I proposed saying the rules may have changed; the AI pointed out that the orders postdate the manual, so I chose its alternative: state the current rule, say the reason is unknown and offer to escalate.
- **Fixed by me:** I replaced `.gitignore`, which held a copy of the README, so `.env` was not ignored. I also renamed the PDF to `data/policies.pdf`.

## Step 2: Tools and tests

- **Asked:** `get_order`, `search_products` and their schemas in `src/tools.py`, with pytest tests on the real data, from a detailed specification I wrote. I asked the AI to check the specification against the CSVs before coding.
- **Accepted:** the generated tools and tests; the finding that no product name contains the instrument type, so my "violao" query test could not pass; and the finding that only 7 of the 10 descriptions of products 135-144 contradict the name. I kept all 10 excluded because they come from the same batch.
- **Adjusted:** I rejected the AI's fix for the search (matching name plus category name, a "violao" alias and category substrings). I replaced it with an enum of the 9 categories, exact category equality and `query` matching only the product name. The AI also reported that numbers with +55 failed verification, so I added a rule that drops the country code but still requires the area code. I reworded the README bullet on products 135-144 to call the descriptions unreliable.

## Step 3: Agent and CLI

- **Asked:** `src/agent.py` and `src/main.py` from a detailed specification I wrote, covering the system prompt, the tool-calling loop, error handling and debug mode, plus "How to run" in the README and a real run of six test messages.
- **Accepted:** the generated agent and CLI, including what the AI added beyond my specification: the rule from step 1 for orders below the installment minimums, a 120s timeout and a single API retry.
- **Adjusted:** the first runs failed on the free tier limits of `gemini-3.8-flash`, so I switched `.env` to `gemini-3.6-flash`. The AI then found that the remaining failures came from a limit of 5 requests per minute and reran messages 4 to 6 with pauses. All six messages passed on 3.6; 3.8 was not fully tested.

