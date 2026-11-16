# Registration page tests

This repository holds only three things:

| What | Where |
|---|---|
| Registration application (system under test) | `aut/` |
| Execution test cases (Gherkin) and their step definitions | `tests/features/`, `tests/steps/` |
| Execution test reports | `reports/` |

Feature files and reports are added by the QA Test Case Generator Agent, after a human approves them.

## Run it
```bash
pip install -r requirements.txt
playwright install chromium
python aut/serve.py          # registration page at http://localhost:8000 (leave running)
pytest                       # in a second terminal
```
Set `AUT_URL` to test a page served somewhere else.
