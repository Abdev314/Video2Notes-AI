"""
Export to Markdown.

Renders the enriched Segments into a clean Markdown document using a
Jinja2 templates. Supports both relative paths (for web viewing) and
base64 embedded images (for PDF/Word export).
"""

from __future__ import annotations

import base64
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


# Image handling helpers

def _image_to_base64(image_path: Path) -> str | None:
    """
    Convert image file to base64 data URI.

    Returns a data URI like: data:image/jpeg;base64,/9j/4AAQSkZ...
    This can be embedded directly in markdown/HTML and works with PDF converters.
    """
    if not image_path or not image_path.exists():
        return None

    try:
        # Determine MIME type based on file extension
        suffix = image_path.suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
        }.get(suffix, 'image/jpeg')

        with open(image_path, "rb") as img_file:
            b64_data = base64.b64encode(img_file.read()).decode()

        return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        log.warning(f"Failed to embed image {image_path}: {e}")
        return None


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
        If True, embed images as base64 (for PDF/Word export).
        If False, use relative paths (for web viewing).
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

    # Build view-model for templates
    segment_views = []
    for seg in segments:
        # Ensure frame_path is a Path object
        frame_path = Path(seg.frame_path) if seg.frame_path else None

        # Determine image source based on embed_frames setting
        if frame_path and frame_path.exists() and embed_frames:
            # Embed as base64 (for PDF/Word export)
            frame_src = _image_to_base64(frame_path)
        elif frame_path and frame_path.exists() and not embed_frames:
            # Use relative path (for web viewing)
            frame_src = _relative_to(frame_path, output_path.parent)
        else:
            frame_src = None

        view = {
            "id": seg.id,
            "title": seg.title,
            "timestamp_label": seg.timestamp_label,
            "duration": seg.duration,
            "summary": seg.summary,
            "key_points": seg.key_points,
            "transcript": seg.transcript,
            "frame_src": frame_src,
        }
        segment_views.append(view)

    log.info(
        f"Rendering [cyan]{len(segments)}[/cyan] segments "
        f"to [cyan]{output_path.name}[/cyan] "
        f"(embed_frames=[yellow]{embed_frames}[/yellow], "
        f"include_transcript=[yellow]{include_transcript}[/yellow])"
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