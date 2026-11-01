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
data/      original challenge files (never modified)
docs/      project documentation
```

_More folders will be added as the project evolves._

## How to run

_TBD_

## Technical decisions

_TBD_

## Assumptions and data handling

_TBD_

## Known limitations and future work

_TBD_

## Use of AI coding assistants

_TBD_