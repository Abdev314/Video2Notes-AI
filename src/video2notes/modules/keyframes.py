"""
Step 5 of the pipeline — keyframe extraction.

For each Segment, seeks into the video and saves one representative frame
as a JPEG. Attaches the saved path back to the Segment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import cv2

from video2notes.models.segment import Segment
from video2notes.utils.logger import get_logger

log = get_logger(__name__)


class KeyframeExtractionError(RuntimeError):
    """Raised when the video cannot be opened for keyframe extraction."""


Position = Literal["start", "middle", "end"]

# feat: implement keyframe extraction module


def extract_keyframes(
    video_path: Path,
    segments: list[Segment],
    output_dir: Path,
    *,
    position: Position = "middle",
    quality: int = 90,
    max_width: int = 1280,
) -> list[Segment]:
    """
    Extract one keyframe per segment.

    Parameters
    ----------
    video_path : Path
        Path to the source video.
    segments : list[Segment]
        Segments to extract frames for.
    output_dir : Path
        Directory to write JPEGs into (created if missing).
    position : "start" | "middle" | "end"
        Which timestamp inside the segment to grab.
    quality : int
        JPEG quality 1-100.
    max_width : int
        Frames wider than this are downscaled, preserving aspect ratio.

    Returns
    -------
    list[Segment] : the same segments with `frame_path` filled in.

    Raises
    ------
    FileNotFoundError : if the video doesn't exist.
    KeyframeExtractionError : if the video can't be opened.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info(
        f"Extracting [cyan]{len(segments)}[/cyan] keyframes "
        f"from [cyan]{video_path.name}[/cyan] "
        f"(position=[yellow]{position}[/yellow])"
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise KeyframeExtractionError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0  # fallback if metadata is missing

    try:
        for seg in segments:
            timestamp = _pick_timestamp(seg.start_time, seg.end_time, position)
            frame_path = output_dir / f"segment_{seg.id:03d}.jpg"

            frame = _grab_frame(cap, timestamp, fps)
            if frame is None:
                log.warning(
                    f"[yellow]No frame at {timestamp:.2f}s for segment #{seg.id}[/yellow]"
                )
                continue

            if frame.shape[1] > max_width:
                frame = _resize_keeping_aspect(frame, max_width)

            ok = cv2.imwrite(
                str(frame_path), frame,
                [cv2.IMWRITE_JPEG_QUALITY, quality],
            )
            if not ok:
                log.warning(
                    f"[yellow]Failed to write frame for segment #{seg.id}[/yellow]"
                )
                continue

            seg.frame_path = frame_path
    finally:
        cap.release()

    saved = sum(1 for s in segments if s.frame_path is not None)
    log.info(
        f"[green]✓ Saved {saved}/{len(segments)} keyframes[/green] "
        f"to [cyan]{output_dir}[/cyan]"
    )
    return segments


# Helpers

def _pick_timestamp(start: float, end: float, position: Position) -> float:
    """Return which second inside [start, end] to grab the frame from."""
    if position == "start":
        return start
    if position == "end":
        # Pull back 100 ms so we don't grab the transition into the next scene
        return max(start, end - 0.1)
    return (start + end) / 2.0   # middle


def _grab_frame(cap: cv2.VideoCapture, timestamp: float, fps: float):
    """Seek to `timestamp` (seconds) and read one frame. Returns None on failure."""
    # Primary: seek by milliseconds (works on most formats)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    ok, frame = cap.read()
    if ok and frame is not None:
        return frame

    # Fallback: seek by frame number (some codecs ignore MSEC)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(timestamp * fps))
    ok, frame = cap.read()
    return frame if ok else None


def _resize_keeping_aspect(frame, max_width: int):
    """Downscale to `max_width` while preserving aspect ratio."""
    h, w = frame.shape[:2]
    new_h = int(h * (max_width / w))
    return cv2.resize(frame, (max_width, new_h), interpolation=cv2.INTER_AREA)