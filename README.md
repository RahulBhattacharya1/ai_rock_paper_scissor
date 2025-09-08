# Rock–Paper–Scissors

Play RPS against an offline heuristic or an OpenAI opponent.

## Features
- Offline AI counters your most frequent recent choice
- Optional OpenAI mode (expects `{"choice":"rock|paper|scissors"}`)
- Guardrails: cooldown, daily limit, hourly cap, daily budget
- Remote config via `BUDGET_URL`

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# optional:
mkdir -p .streamlit && printf 'OPENAI_API_KEY = "sk-..."\n' > .streamlit/secrets.toml
streamlit run app.py
