# AGENTS.md

Guidance for AI coding assistants working in this repository.

## Project

Prototype customer service agent for "Empório da Música", a fictional musical instrument store (Artefact AI Engineer technical challenge). The evaluators explicitly value **the simplest possible solution**: every file, dependency and abstraction must justify its existence.

## Architecture

"Facts that change come from tools; stable rules live in the prompt." Whatever can be deterministic is computed in Python, not left to the LLM.

- Exactly two tools, called via native function calling (no agent frameworks):
  - `search_products`: search by product name (`query`) and category, with price and availability filters. Applies active promotions and returns the final price, the PIX price and the maximum interest-free installments with their value. When a query matches no available product, it also returns the unavailable matches and up to 3 real alternatives (same category, price within ±30%). The `category` enum lists only categories that have products.
  - `get_order`: order lookup that requires the order number **and** the customer's email or phone. Returns the delivery forecast and the exchange and warranty deadlines, computed in Python.
- The system prompt holds the full policy manual (`data/policies.md`, with the README decisions applied; no retrieval), the current date and the store's open/closed status, computed in Python.
- LLM accessed through an OpenAI-compatible API, configured only via `.env`: DeepSeek (`deepseek-flash`) by default, Gemini as an alternative by changing the `LLM_*` variables. No provider-specific parameters in the code.
- Simple CLI interface; conversation history kept in memory during the session.

## Conventions

- **Language:** code identifiers, comments, docs and commit messages in English. Everything the customer sees (system prompt, agent replies, tool parameter descriptions) in Brazilian Portuguese.
- Python 3.11+, few dependencies (`openai`, `pandas`, `python-dotenv`, `pytest`).
- Prefer small functions over classes and dicts over models. Use type hints.
- Tools are pure functions, testable without the LLM, with pytest tests.
- All arithmetic (discounts, PIX price, installments, date differences) is done in Python, never by the LLM.
- Customer-facing formats: `R$ 1.299,90` and `DD/MM/AAAA`.

## Rules

- Never modify the original files in `data/`.
- API keys only in `.env` (never committed). Keep `.env.example` up to date.
- Do not add dependencies, files, tools or features without a requirement that needs them.
- Example conversations in `examples/` must come from real runs, never written by hand.
- Data and manual inconsistencies are documented in the README, not silently "fixed".