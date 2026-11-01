# AGENTS.md

Guidance for AI coding assistants working in this repository.

## Project

Prototype customer service agent for "Empório da Música", a fictional musical instrument store (Artefact AI Engineer technical challenge). The evaluators explicitly value **the simplest possible solution**: every file, dependency and abstraction must justify its existence.

## Architecture

"Facts that change come from tools; stable rules live in the prompt."

- Exactly two tools, called via native function calling (no agent frameworks):
  - `search_products`: product search with price/category/availability filters and active promotions applied.
  - `get_order`: order lookup that requires the order number **and** the customer's email or phone.
- The full store policy manual goes in the system prompt (no retrieval).
- LLM accessed through an OpenAI-compatible API, configured via `.env`.
- Simple CLI interface; conversation history kept in memory during the session.

## Conventions

- **Language:** code identifiers, comments, docs and commit messages in English. Everything the customer sees (system prompt, agent replies, tool parameter descriptions) in Brazilian Portuguese.
- Python 3.11+, few dependencies (`openai`, `pandas`, `python-dotenv`, `pytest`).
- Prefer small functions over classes and dicts over models. Use type hints.
- Tools are pure functions, testable without the LLM, with pytest tests.
- All arithmetic (discounts, PIX price, date differences) is done in Python, never by the LLM.
- Customer-facing formats: `R$ 1.299,90` and `DD/MM/AAAA`.

## Rules

- Never modify the original files in `data/`.
- API keys only in `.env` (never committed). Keep `.env.example` up to date.
- Do not add dependencies, files, tools or features without a requirement that needs them.
- Example conversations in `examples/` must come from real runs, never written by hand.
- Data and manual inconsistencies are documented in the README, not silently "fixed".