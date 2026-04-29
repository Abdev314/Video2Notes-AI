"""
segment builder.

Combines the output of Phase 4 (timestamped utterances from Whisper)
with the output of Phase 5 (scene boundaries from PySceneDetect) into
Segment objects, which are the pipeline's chapter unit.
"""

from __future__ import annotations

from src.models.segment import Segment


from src.modules.transcribe import Utterance
from src.utils.logger import get_logger

log = get_logger(__name__)


def build_segments(
    scenes: list[tuple[float, float]],
    utterances: list[Utterance],
) -> list[Segment]:
    """
    Merge scene boundaries and utterances into Segment objects.

    Parameters
    ----------
    scenes : list of (start, end) tuples from detect_scenes()
    utterances : list of Utterance objects from transcribe_audio()

    Returns
    -------
    list[Segment] : one Segment per scene, with utterances assigned by
                    their start timestamp.
    """
    if not scenes:
        log.warning("[yellow]No scenes provided — returning empty segment list[/yellow]")
        return []

    log.info(
        f"Building segments from [cyan]{len(scenes)}[/cyan] scenes "
        f"and [cyan]{len(utterances)}[/cyan] utterances"
    )

    # Pre-sort utterances by start time (they already are, but be safe)
    utterances = sorted(utterances, key=lambda u: u.start)

    segments: list[Segment] = []

    # Pointer into utterances — avoids O(n²) by walking through once
    u_idx = 0

    for i, (start, end) in enumerate(scenes, start=1):
        scene_utterances: list[Utterance] = []

        # Skip utterances that end before this scene starts
        # (shouldn't normally happen, but handles weird edge cases)
        while u_idx < len(utterances) and utterances[u_idx].start < start:
            u_idx += 1

        # Collect utterances whose start falls inside this scene
        while u_idx < len(utterances) and utterances[u_idx].start < end:
            scene_utterances.append(utterances[u_idx])
            u_idx += 1

        transcript = " ".join(u.text for u in scene_utterances).strip()

        segment = Segment(
            id=i,
            start_time=start,
            end_time=end,
            transcript=transcript,
        )
        segments.append(segment)

    # Log a quick summary
    with_text = sum(1 for s in segments if s.transcript)
    log.info(
        f"[green]✓ Built {len(segments)} segments[/green] "
        f"([cyan]{with_text}[/cyan] with transcript, "
        f"[dim]{len(segments) - with_text} silent[/dim])"
    )

    return segments