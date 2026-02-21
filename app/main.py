from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.ledger import ensure_ledger_exists

app = FastAPI(title="Checksum Registry", version="0.1")


@app.on_event("startup")
def on_startup() -> None:
    ensure_ledger_exists()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang=\"ja\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Checksum Registry v0.1</title>
  </head>
  <body>
    <h1>Checksum Registry v0.1</h1>
  </body>
</html>
"""


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
