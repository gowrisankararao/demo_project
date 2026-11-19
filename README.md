# Alert Explainer API

A FastAPI service that stores alerts and returns rule-based explanations built
from each alert's fields. The explanation logic uses fixed rules; it does not
call an external AI or LLM service.

## Project structure

```text
.
├── database.py          # SQLite engine, session dependency, and ORM base
├── main.py              # FastAPI application and router registration
├── models.py            # SQLAlchemy Alert model
├── requirements.txt     # Runtime dependencies
├── .gitignore
├── routers/
│   ├── __init__.py
│   └── alerts.py        # Alert and explanation endpoints
├── schemas.py           # Pydantic request and response schemas
├── services/
│   ├── __init__.py
│   └── explainer.py     # Rule-based explanation logic
├── test_alerts.py       # API tests
└── docs/
    └── adr/
        ├── 0001-rule-based-explanations.md
        └── 0002-human-approval-for-alert-summaries.md
```

The SQLite database is created as `alerts.db` in the working directory when
the application starts.

## Alert fields

Create an alert with these fields:

| Field | Type | Description |
|---|---|---|
| `title` | string | Alert title |
| `severity` | string | One of `critical`, `warning`, or `info`, as restricted by the Pydantic request schema |
| `source` | string | Source that raised the alert |
| `metric_name` | string | Name of the measured metric |
| `metric_value` | number | Current metric value |
| `threshold` | number | Threshold used by the explanation rules |

The SQLAlchemy model stores `severity` as a string; the allowed values are
validated by the Pydantic schema. Alert responses also include `id` and
`created_at`.

The explanation compares `metric_value` with `threshold`, uses `severity` to
choose a recommended next step, and includes the alert's title, source, and
metric. If there is no acknowledged-by value, the explanation says
`Not yet acknowledged`.

## API endpoints

All paths below are relative to the service root.

| Method | Path | Success | Other status codes | Description |
|---|---|---:|---|---|
| `GET` | `/` | 200 | — | Health message |
| `POST` | `/alerts/` | 201 | 422 for invalid request data | Create an alert |
| `GET` | `/alerts/` | 200 | — | List alerts |
| `GET` | `/alerts/{alert_id}` | 200 | 404 if the alert does not exist; 422 for an invalid path value | Retrieve an alert |
| `POST` | `/alerts/{alert_id}/explain` | 200 | 404 if the alert does not exist; 422 for an invalid path value | Generate a rule-based explanation |

Missing alerts return a 404 response with the detail `Alert not found`.
Explanation responses contain `alert_id`, `explanation`, and `generated_at`.
Interactive API documentation is available at `/docs`.

## Install and run on Windows (PowerShell)

From the project directory:

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt pytest httpx
uvicorn main:app --reload
```

Uvicorn serves the API at `http://127.0.0.1:8000`. Open
`http://127.0.0.1:8000/docs` for Swagger UI. Stop the server with `Ctrl+C`.

## Run the tests

With the virtual environment activated, run:

```powershell
python -m pytest test_alerts.py -v
```

## Architecture Decision Records

- [ADR 0001: Rule-based explanations](docs/adr/0001-rule-based-explanations.md)
- [ADR 0002: Human approval for alert summaries](docs/adr/0002-human-approval-for-alert-summaries.md)
