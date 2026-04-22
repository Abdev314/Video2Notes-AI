"""
`.

Wraps the 7-step pipeline so users can run the whole tool from the
command line without writing any Python.
"""

from __future__ import annotations

from pathlib import Path

import click

from modules.audio import extract_audio
from modules.transcribe import transcribe_audio
from modules.scenes import detect_scenes
from modules.segments import build_segments
from modules.keyframes import extract_keyframes
from modules.ai import analyze_segments, AIAnalysisError
from modules.export import export_markdown
from utils.config import load_config
from utils.logger import get_logger


@click.command()
@click.argument(
    "video",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=Path("output/notes.md"),
    show_default=True,
    help="Where to write the markdown notes.",
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="Skip AI summarization (faster; produces transcripts without titles).",
)
@click.option(
    "--config",
    type=click.Path(path_type=Path),
    default=Path("config.yaml"),
    show_default=True,
    help="Path to config file.",
)
def main(video: Path, output: Path, no_ai: bool, config: Path) -> None:

    log = get_logger("video2notes")
    cfg = load_config(config)

    cache_dir = Path(cfg.paths.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    audio_path = cache_dir / f"{video.stem}.wav"
    frames_dir = output.parent / "frames"

    log.info(f"[bold]Processing[/bold] [cyan]{video.name}[/cyan]")

    # ---- 7-step pipeline ----
    extract_audio(video, audio_path)

    utterances = transcribe_audio(
        audio_path,
        model_size=cfg.whisper.model_size,
        language=cfg.whisper.language,
        device=cfg.whisper.device,
        compute_type=cfg.whisper.compute_type,
    )

    scenes = detect_scenes(
        video,
        threshold=cfg.scenes.threshold,
        min_scene_length=cfg.scenes.min_scene_length,
    )

    segments = build_segments(scenes, utterances)

    segments = extract_keyframes(
        video, segments, frames_dir,
        position=cfg.keyframes.position,
        quality=cfg.keyframes.quality,
        max_width=cfg.keyframes.max_width,
    )

    if cfg.ai.enabled and not no_ai:
        try:
            segments = analyze_segments(
                segments,
                model=cfg.ai.model,
                base_url=cfg.ai.base_url,
                temperature=cfg.ai.temperature,
                max_retries=cfg.ai.max_retries,
            )
        except AIAnalysisError as e:
            log.error(f"[red]AI step failed:[/red] {e}")
            log.warning("Continuing without titles/summaries…")
    else:
        log.info("[dim]AI step skipped[/dim]")

    export_markdown(
        segments, output,
        title=_pretty_title(video.stem),
        embed_frames=cfg.output.embed_frames,
        include_transcript=cfg.output.include_transcript,
    )

    log.info(f"[bold green]✓ Done.[/bold green] Open: [cyan]{output}[/cyan]")


def _pretty_title(stem: str) -> str:
    """Convert 'my_lecture-01' → 'My Lecture 01 — Notes'."""
    return stem.replace("_", " ").replace("-", " ").title() + " — Notes"


if __name__ == "__main__":
    main()