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
    title="returns",
    version="0.1.0",
    description=(
        "Reference return-filing service for the Sovereign Revenue Data "
        "Exchange. Accepts synthetic tax returns indexed by TIN and period."
    ),
    lifespan=lifespan,
)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok", "service": "returns"}


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
