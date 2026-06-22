from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from . import db, fixtures
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    fixtures.seed_if_empty()
    yield


app = FastAPI(
    title="taxpayer-registry",
    version="0.1.0",
    description=(
        "Reference taxpayer registry service for the Sovereign Revenue Data "
        "Exchange. Holds synthetic taxpayer records keyed by TIN, supports "
        "lookup by NID, and provides candidate deduplication."
    ),
    lifespan=lifespan,
)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok", "service": "taxpayer-registry"}


app.include_router(router)


def export_openapi(target: Path) -> Path:
    """Write the OpenAPI spec to disk. Used by the Dockerfile build."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), indent=2))
    return target


if __name__ == "__main__":
    # `python -m app.main openapi /out/openapi.json` writes the spec to disk.
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "openapi":
        out = export_openapi(Path(sys.argv[2]))
        print(f"wrote {out}")
    else:
        import uvicorn

        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
