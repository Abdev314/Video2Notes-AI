"""
Export to Markdown.

Renders the enriched Segments into a clean Markdown document using a
Jinja2 templates. Image paths are made relative to the output file so
the markdown is portable (can be moved or converted to HTML/PDF without
breaking image links).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.models.segment import Segment
from src.utils.logger import get_logger

log = get_logger(__name__)


class ExportError(RuntimeError):
    """Raised when rendering or writing the output file fails."""


# Template loading

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _make_env() -> Environment:
    """Create a Jinja2 environment pointed at our templates folder."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,               # markdown is plain text, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,      # raises on missing variables — fail loudly
    )


# Public API

def export_markdown(
    segments: Iterable[Segment],
    output_path: Path,
    *,
    title: str = "Video Notes",
    subtitle: str | None = None,
    embed_frames: bool = True,
    include_transcript: bool = False,
) -> Path:
    """
    Render the segments into a Markdown file.

    Parameters
    ----------
    segments : Iterable[Segment]
        Enriched segments with titles, summaries, and keyframes.
    output_path : Path
        Where to write the .md file. Parent dirs are created if missing.
    title : str
        Main heading of the document.
    subtitle : str | None
        Optional italic line under the title.
    embed_frames : bool
        If True, include keyframe images in the output.
    include_transcript : bool
        If True, include each segment's full transcript under a <details> block.

    Returns
    -------
    Path : resolved path to the written Markdown file.

    Raises
    ------
    ExportError : if rendering or file writing fails.
    """
    segments = list(segments)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Attach `frame_rel_path` to each segment so the templates can use it.
    # Relative to output_path's parent, so `output/notes.md` will point to
    # `frames/segment_001.jpg` — not an absolute path.
    # Attach `frame_rel_path` to each segment so the templates can use it.
    # Build a lightweight view-model for the templates.
    # We don't mutate Segment — we just package the data the templates needs.
    segment_views = [
        {
            "id": seg.id,
            "title": seg.title,
            "timestamp_label": seg.timestamp_label,
            "duration": seg.duration,
            "summary": seg.summary,
            "key_points": seg.key_points,
            "transcript": seg.transcript,
            "frame_rel_path": (
                _relative_to(seg.frame_path, output_path.parent)
                if seg.frame_path is not None else None
            ),
        }
        for seg in segments
    ]

    log.info(
        f"Rendering [cyan]{len(segments)}[/cyan] segments "
        f"to [cyan]{output_path.name}[/cyan] "
        f"(frames=[yellow]{embed_frames}[/yellow], "
        f"transcript=[yellow]{include_transcript}[/yellow])"
    )

    try:
        env = _make_env()
        template = env.get_template("notes.md.j2")
        rendered = template.render(
            title=title,
            subtitle=subtitle,
            segments=segment_views,
            embed_frames=embed_frames,
            include_transcript=include_transcript,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
    except Exception as e:
        raise ExportError(f"Template rendering failed: {e}") from e

    try:
        output_path.write_text(rendered, encoding="utf-8")
    except OSError as e:
        raise ExportError(f"Failed to write {output_path}: {e}") from e

    size_kb = output_path.stat().st_size / 1024
    log.info(
        f"[green]✓ Wrote[/green] [cyan]{output_path}[/cyan] "
        f"([yellow]{size_kb:.1f} KB[/yellow])"
    )
    return output_path


# Helpers

def _relative_to(target: Path, base: Path) -> str:
    """
    Return `target` as a forward-slash path relative to `base`.
    Falls back to the absolute path if they're on different drives.
    """
    target = Path(target).resolve()
    base = Path(base).resolve()
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        return target.as_posix()