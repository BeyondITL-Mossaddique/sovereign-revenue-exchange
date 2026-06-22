from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="exchange-gateway",
    version="0.1.0",
    description=(
        "Reference inter-agency exchange gateway. Composes the taxpayer "
        "registry and returns services into a single governed read surface, "
        "and verifies claims about a taxpayer's return status for a "
        "requesting agency. Synthetic data only."
    ),
)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok", "service": "exchange-gateway"}


app.include_router(router)


def export_openapi(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), indent=2))
    return target


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "openapi":
        out = export_openapi(Path(sys.argv[2]))
        print(f"wrote {out}")
    else:
        import uvicorn

        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
