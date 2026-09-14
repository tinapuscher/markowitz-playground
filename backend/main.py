"""FastAPI backend for the Markowitz playground."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from asset_resolver import ResolverError, resolve_asset
from sample_portfolio import optimize_sample_portfolio


class SampleOptimizationRequest(BaseModel):
    wkns: list[str]


app = FastAPI(
    title="Markowitz Playground API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
    }


@app.get("/api/resolve/{identifier}")
async def resolve(identifier: str):
    try:
        asset = await resolve_asset(identifier)

        return {
            "status": "resolved",
            "asset": asdict(asset),
        }

    except ResolverError as exc:
        status_code = 503 if (
            exc.code == "MARKET_DATA_PROVIDER_UNAVAILABLE"
        ) else 422

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "code": exc.code,
            },
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "INTERNAL_ERROR",
            },
        )


@app.post("/api/optimize/sample")
async def optimize_sample(
    request: SampleOptimizationRequest,
):
    try:
        result = optimize_sample_portfolio(
            selected_wkns=request.wkns,
        )

        return {
            "status": "ok",
            "result": asdict(result),
        }

    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "code": "INVALID_SAMPLE_SELECTION",
                "message": str(exc),
            },
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "OPTIMIZATION_FAILED",
            },
        )