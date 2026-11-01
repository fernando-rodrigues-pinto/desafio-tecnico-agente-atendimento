# AI-assisted workflow log

Log of how AI coding assistants were used in this project: what was asked, what was accepted and what was adjusted. 

**Tool:** Claude (claude.ai, Claude Opus 5.5), used as pair programmer. All generated code and text is reviewed.

## Step 0: Initial setup

- **Asked:** a repository description and the initial structure (README, AGENTS.md, .gitignore).
- **Accepted:** documentation and code identifiers in English; only customer-facing content (prompt, replies) in Portuguese. Tools renamed to `search_products` and `get_order`.
- **Adjusted:** minor details in text.

## Step 1: Setup and store policy manual

- **Asked:** `requirements.txt`, `.env.example`, a Markdown version of the policy PDF, and each manual inconsistency presented one at a time for a decision.
- **Accepted:** dependency versions (latest on PyPI, tested in a throwaway venv); the AI's recommended option for the email, installments, partner stores, catalog claims, defects after 30 days, free shipping threshold, preference exchanges and promotions data.
- **Adjusted:** the user chose the section 7 WhatsApp number, not the AI's recommended option. The user first asked for a verbatim manual, then changed `data/policies.md` to reflect the decisions; every change from the PDF is listed in the README and was checked with a word-level comparison. The AI asked to add inconsistencies it found beyond the user's list (f to j). For orders below the installment minimums, the user proposed saying the rules may have changed; the AI objected because the orders postdate the manual, and the user chose stating the current rule, saying the reason is unknown and offering to escalate.
- **Fixed by the user:** `.gitignore` held a copy of the README, so `.env` was not ignored; the AI flagged it and the user replaced the file. The user also renamed the PDF to `data/policies.pdf`.

