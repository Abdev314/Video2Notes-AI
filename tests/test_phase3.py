"""Smoke test for Phase 3 — audio extraction. Delete once green."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.audio import extract_audio, AudioExtractionError
from src.utils.logger import get_logger


def main() -> None:
    log = get_logger("phase3_test")
    log.info("[bold green]Phase 3 smoke test — audio extraction[/bold green]")

    video_path = Path("data/sample.mp4")
    output_path = Path("output/sample.wav")

    if not video_path.exists():
        log.error(f"[red]No test video found at {video_path}[/red]")
        log.error("Drop a small .mp4 into data/sample.mp4 and rerun.")
        sys.exit(1)

    # 1. Happy path
    try:
        result = extract_audio(video_path, output_path)
        log.info(f"[green]✓ Output created:[/green] {result}")
    except AudioExtractionError as e:
        log.error(f"[red]Extraction failed:[/red] {e}")
        sys.exit(1)

    # 2. Sad path — nonexistent input should raise FileNotFoundError
    try:
        extract_audio(Path("data/does_not_exist.mp4"), Path("output/nope.wav"))
    except FileNotFoundError:
        log.info(
            "[green]✓ FileNotFoundError correctly raised for missing input[/green]"
        )
    else:
        log.error("[red]Expected FileNotFoundError was not raised[/red]")
        sys.exit(1)

    log.info("[bold green]✅ Phase 3 is working![/bold green]")


if __name__ == "__main__":
    main()
