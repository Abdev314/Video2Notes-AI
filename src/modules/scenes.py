"""
scene detection

Reads the video stream (not the audio) and identifies timestamps where
the visual content changes significantly. These timestamps will later
be used as chapter boundaries.
"""

from __future__ import annotations

from pathlib import Path

from scenedetect import open_video, SceneManager

from scenedetect.detectors import ContentDetector, AdaptiveDetector

from utils.logger import get_logger

log = get_logger(__name__)


class SceneDetectionError(RuntimeError):
    """Raised when scene detection fails on the given video."""


def detect_scenes(
    video_path: Path,
    *,
    threshold: float = 27.0,
    min_scene_length: float = 30.0,
) -> list[tuple[float, float]]:
    """
    Detect scene boundaries in a video.

    Parameters
    ----------
    video_path : Path
        Path to the video file.
    threshold : float
        Sensitivity (0-100). Lower = more scenes detected.
    min_scene_length : float
        Minimum length in seconds. Scenes shorter than this get merged
        into their neighbor.

    Returns
    -------
    list[tuple[float, float]]
        List of (start_time, end_time) in seconds, covering the full
        video continuously. Guaranteed non-empty.

    Raises
    ------
    FileNotFoundError : if the video doesn't exist.
    SceneDetectionError : if PySceneDetect fails.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    log.info(
        f"Detecting scenes in [cyan]{video_path.name}[/cyan] "
        f"(threshold=[yellow]{threshold}[/yellow], "
        f"min_length=[yellow]{min_scene_length}s[/yellow])"
    )

    try:
        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(
            AdaptiveDetector(
                adaptive_threshold=3.0,
                min_scene_len=int(min_scene_length * video.frame_rate),
            )
        )
        scene_manager.detect_scenes(video, show_progress=False)
        scene_list = scene_manager.get_scene_list()
    except Exception as e:
        raise SceneDetectionError(f"PySceneDetect failed: {e}") from e

    # Convert PySceneDetect's FrameTimecode objects to plain floats
    raw_scenes: list[tuple[float, float]] = [
        (s.get_seconds(), e.get_seconds()) for s, e in scene_list
    ]

    # If no scenes detected, treat the whole video as one scene
    if not raw_scenes:
        duration = video.duration.get_seconds()
        log.warning(
            "[yellow]No scene changes detected — treating video as one scene[/yellow]"
        )
        return [(0.0, duration)]

    log.info(f"Raw scenes detected: [cyan]{len(raw_scenes)}[/cyan]")

    # Merge scenes shorter than min_scene_length into the next one
    merged = _merge_short_scenes(raw_scenes, min_scene_length)

    log.info(
        f"[green]✓ Final scenes after merging:[/green] [cyan]{len(merged)}[/cyan]"
    )
    return merged


def _merge_short_scenes(
    scenes: list[tuple[float, float]],
    min_length: float,
) -> list[tuple[float, float]]:
    """Merge consecutive scenes so that none is shorter than min_length."""
    if not scenes:
        return []

    merged: list[tuple[float, float]] = []
    current_start, current_end = scenes[0]

    for start, end in scenes[1:]:
        current_duration = current_end - current_start
        if current_duration < min_length:
            # Extend the current scene instead of starting a new one
            current_end = end
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    # Handle the last scene — if too short, merge backwards into previous
    last_duration = current_end - current_start
    if last_duration < min_length and merged:
        prev_start, _ = merged.pop()
        merged.append((prev_start, current_end))
    else:
        merged.append((current_start, current_end))

    return merged