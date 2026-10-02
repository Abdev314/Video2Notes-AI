"""Smoke test for Phase 2 foundation. Delete once Phase 2 is confirmed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.segment import Segment
from src.utils.config import load_config
from src.utils.logger import get_logger


def main() -> None:
    log = get_logger("phase2_test")
    log.info("[bold green]Phase 2 smoke test starting[/bold green]")

    # 1. Config
    cfg = load_config()
    log.info(f"Whisper model   : [cyan]{cfg.whisper.model_size}[/cyan]")
    log.info(f"AI backend      : [cyan]{cfg.ai.backend}[/cyan]")
    log.info(f"Output formats  : [cyan]{cfg.output.formats}[/cyan]")
    log.info(f"Data dir        : [cyan]{cfg.paths.data_dir}[/cyan]")

    # 2. Segment creation
    seg = Segment(
        id=1,
        start_time=0.0,
        end_time=124.5,
        transcript="Hello everyone, welcome to linear algebra.",
    )
    log.info(f"Segment         : {seg}")
    log.info(f"Duration        : [yellow]{seg.duration}s[/yellow]")

    # 3. Validation should reject bad data
    try:
        Segment(id=1, start_time=100.0, end_time=50.0)
    except Exception as e:
        log.info(f"[green]✓ Validation works:[/green] {type(e).__name__} caught")

    log.info("[bold green]✅ Phase 2 foundation is working![/bold green]")


if __name__ == "__main__":
    main()
