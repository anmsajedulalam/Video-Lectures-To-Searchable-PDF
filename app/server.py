"""FastAPI application exposing the pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import IngestRequest, resolve_settings
from .pipeline import PipelineResult, PipelineRunner

app = FastAPI(title="Video Lectures to Searchable PDFs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

runner = PipelineRunner(resolve_settings())


class PipelineResponse(BaseModel):
    video_id: str
    slide_pdf: str
    transcript_pdf: str
    combined_pdf: str

    @classmethod
    def from_result(cls, result: PipelineResult) -> "PipelineResponse":
        return cls(
            video_id=result.video_id,
            slide_pdf=str(result.slide_pdf),
            transcript_pdf=str(result.transcript_pdf),
            combined_pdf=str(result.combined_pdf),
        )


@app.post("/process", response_model=PipelineResponse)
def process(request: IngestRequest) -> PipelineResponse:
    try:
        result = runner.run(request)
    except Exception as exc:  # pragma: no cover - API error path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return PipelineResponse.from_result(result)

