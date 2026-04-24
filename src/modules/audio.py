"""
Audio extraction.

Takes a video file of any format (.mp4, .mkv, .webm, etc.) and produces a
16 kHz mono WAV file, which is the native input format of Whisper.

The heavy lifting is done by FFmpeg via a subprocess call.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from utils.logger import get_logger

log = get_logger(__name__)


class AudioExtractionError(RuntimeError):
    """Raised when FFmpeg fails to produce audio from the input video."""


def ensure_ffmpeg_available() -> None:
    """Fail fast with a helpful message if FFmpeg isn't on PATH."""
    if shutil.which("ffmpeg") is None:
        raise AudioExtractionError(
            "FFmpeg not found on PATH.\n"
        )


def extract_audio(
    video_path: Path,
    output_path: Path,
    *,
    sample_rate: int = 16000,
    channels: int = 1,
    overwrite: bool = True,
) -> Path:
    """
    Extract the audio track of a video into a WAV file.

    Parameters
    ----------
    video_path : Path
        Source video (.mp4, .mkv, .webm, ...).
    output_path : Path
        Destination WAV file. Parent directory is created if missing.
    sample_rate : int
        Target sample rate in Hz. 16000 is Whisper's native rate.
    channels : int
        1 = mono, 2 = stereo. Whisper expects mono.
    overwrite : bool
        If True, replaces the output file when it exists.

    Returns
    -------
    Path : the resolved path to the generated WAV file.

    Raises
    ------
    FileNotFoundError : if `video_path` doesn't exist.
    AudioExtractionError : if FFmpeg exits with a non-zero code.
    """
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    ensure_ffmpeg_available()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                          # drop video stream
        "-ac", str(channels),           # audio channels
        "-ar", str(sample_rate),        # sample rate
        "-f", "wav",                    # force WAV container
        "-loglevel", "error",           # only print real errors
        "-hide_banner",
    ]
    if overwrite:
        cmd.append("-y")
    else:
        cmd.append("-n")
    cmd.append(str(output_path))

    log.info(
        f"Extracting audio: [cyan]{video_path.name}[/cyan] "
        f"→ [cyan]{output_path.name}[/cyan] "
        f"([yellow]{sample_rate} Hz, {channels}ch[/yellow])"
    )

    try:
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True,
        )
    except FileNotFoundError as e:
        # Race condition: ffmpeg disappeared between the which() check and now
        raise AudioExtractionError(f"FFmpeg launch failed: {e}") from e

    if result.returncode != 0:
        stderr = result.stderr.strip() or "(no stderr output)"
        raise AudioExtractionError(
            f"FFmpeg failed (exit {result.returncode}):\n{stderr}"
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise AudioExtractionError(
            f"FFmpeg reported success but the output file is missing or empty: "
            f"{output_path}"
        )

    size_mb = output_path.stat().st_size / 1_000_000
    log.info(
        f"[green]✓ Audio extracted[/green] "
        f"([yellow]{size_mb:.1f} MB[/yellow])"
    )
    return output_path