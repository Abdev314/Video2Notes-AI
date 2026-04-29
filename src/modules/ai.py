"""
AI analysis.

For each Segment, asks a local LLM (via Ollama) to produce:
  - a chapter title
  - a concise summary
  - a list of key points

The LLM is forced to output valid JSON via Ollama's native `format="json"`
parameter. The output is validated with Pydantic. On malformed output the
call is retried; if the LLM still misbehaves the segment is left
un-enriched and we continue.
"""

from __future__ import annotations

import json
from typing import Optional

import ollama
from pydantic import BaseModel, Field, ValidationError

from src.models.segment import Segment
from src.utils.logger import get_logger

log = get_logger(__name__)


class AIAnalysisError(RuntimeError):
    """Raised when the LLM backend is unreachable or misconfigured."""


# ------------------------------------------------------------
# Expected JSON shape from the LLM
# ------------------------------------------------------------

class _LLMResponse(BaseModel):
    """Strict schema the LLM is asked to match."""
    title: str = Field(..., min_length=2, max_length=120)
    summary: str = Field(..., min_length=10, max_length=800)
    key_points: list[str] = Field(default_factory=list, max_length=6)


# ------------------------------------------------------------
# The system prompt
# ------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a note-taking assistant for educational content.

You receive the transcript of ONE segment from a longer lecture/tutorial
and must summarize it into study notes.

Respond with a single JSON object and NOTHING else. The JSON MUST have:
  - "title": a short chapter title (2-8 words)
  - "summary": 2-3 sentences covering the segment's main idea
  - "key_points": an array of 2-5 short bullet-point takeaways

Rules:
  - Use the same language as the transcript.
  - Be faithful to the transcript — do NOT invent facts.
  - Keep every field concise. No markdown, no prefixes like "Summary:".
"""


def analyze_segments(
    segments: list[Segment],
    *,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.3,
    max_retries: int = 2,
) -> list[Segment]:
    """
    Enrich each Segment with an AI-generated title, summary, and key points.

    Parameters
    ----------
    segments : list[Segment]
        Segments whose `transcript` is already populated.
    model : str
        Ollama model tag (e.g. "llama3.1:8b", "mistral:7b", "llama3.2:3b").
    base_url : str
        Ollama server URL.
    temperature : float
        Sampling temperature. 0.3 = mostly deterministic.
    max_retries : int
        How many extra attempts on malformed output per segment.

    Returns
    -------
    list[Segment] : same segments, with title/summary/key_points filled in.

    Raises
    ------
    AIAnalysisError : if Ollama is unreachable or the model isn't installed.
    """
    if not segments:
        return segments

    client = ollama.Client(host=base_url)

    # Fail fast if Ollama isn't reachable or the model isn't pulled
    try:
        available = {m.model for m in client.list().models}
    except Exception as e:
        raise AIAnalysisError(
            f"Cannot reach Ollama at {base_url}.\n"
            f"Is the server running? Try: ollama serve\nError: {e}"
        ) from e

    if model not in available and f"{model}:latest" not in available:
        raise AIAnalysisError(
            f"Model '{model}' is not installed in Ollama.\n"
            f"Install it with: ollama pull {model}\n"
            f"Currently available: {sorted(available) or '(none)'}"
        )

    log.info(
        f"Analyzing [cyan]{len(segments)}[/cyan] segments with "
        f"[cyan]{model}[/cyan] (temperature=[yellow]{temperature}[/yellow])"
    )

    enriched = 0
    skipped = 0

    for seg in segments:
        transcript = seg.transcript.strip()
        if not transcript:
            log.info(f"  Segment #{seg.id}: [dim]empty transcript — skipping[/dim]")
            skipped += 1
            continue

        result = _analyze_one(
            client=client,
            model=model,
            transcript=transcript,
            temperature=temperature,
            max_retries=max_retries,
            segment_id=seg.id,
        )

        if result is None:
            skipped += 1
            continue

        seg.title = result.title
        seg.summary = result.summary
        seg.key_points = result.key_points
        enriched += 1

        log.info(f"  Segment #{seg.id}: [green]{result.title}[/green]")

    log.info(
        f"[green]✓ Enriched {enriched}/{len(segments)} segments[/green] "
        f"([dim]{skipped} skipped[/dim])"
    )
    return segments


# ------------------------------------------------------------
# Internal — handle one segment with retries
# ------------------------------------------------------------

def _analyze_one(
    *,
    client: ollama.Client,
    model: str,
    transcript: str,
    temperature: float,
    max_retries: int,
    segment_id: int,
) -> Optional[_LLMResponse]:
    """Ask the LLM about one segment. Returns None if all retries fail."""

    user_prompt = f"Transcript:\n\n{transcript}"

    for attempt in range(1, max_retries + 2):   # 1 initial + `max_retries` retries
        try:
            response = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",                          # force JSON output
                options={"temperature": temperature},
            )
            raw = response["message"]["content"]
        except Exception as e:
            log.warning(
                f"  Segment #{segment_id} attempt {attempt}: LLM call failed — {e}"
            )
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            log.warning(
                f"  Segment #{segment_id} attempt {attempt}: invalid JSON — {e}"
            )
            continue

        try:
            return _LLMResponse(**data)
        except ValidationError as e:
            log.warning(
                f"  Segment #{segment_id} attempt {attempt}: "
                f"schema validation failed ({e.error_count()} errors)"
            )
            continue

    log.warning(
        f"  Segment #{segment_id}: [red]giving up after "
        f"{max_retries + 1} attempts[/red]"
    )
    return None