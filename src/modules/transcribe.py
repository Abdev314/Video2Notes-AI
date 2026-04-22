"""
speech-to-text transcription.

Wraps faster-whisper to convert a WAV file into a list of timestamped
utterances. Output format is intentionally simple so Step 4 can easily
align these utterances with scene-detected segments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from utils.logger import get_logger

log = get_logger(__name__)


# Data class for a single transcribed utterance
@dataclass
class Utterance:
    """A single piece of transcribed speech with start/end timestamps."""
    start: float        # seconds from start of audio
    end: float          # seconds from start of audio
    text: str           # the transcribed text

    def __str__(self) -> str:
        return f"[{self.start:6.2f}s → {self.end:6.2f}s] {self.text}"


# Custom exception
class TranscriptionError(RuntimeError):
    """Raised when the Whisper model fails to transcribe an audio file."""


# The main function
def transcribe_audio(
    audio_path: Path,
    *,
    model_size: str = "base",
    language: Optional[str] = None,
    device: str = "cpu",
    compute_type: str = "int8",
    beam_size: int = 5,
) -> list[Utterance]:
    """
    Transcribe a WAV file into a list of timestamped utterances.

    Parameters
    ----------
    audio_path : Path
        Path to a 16 kHz mono WAV file (as produced by audio.py).
    model_size : str
        Whisper model size. One of: tiny, base, small, medium, large-v3.
    language : Optional[str]
        ISO language code (e.g. "en", "fr", "ar"). If None, auto-detects.
    device : str
        "cpu" or "cuda".
    compute_type : str
        Quantization level. "int8" is the sweet spot on CPU.
    beam_size : int
        Beam search width. 5 is a good default; higher is slower but
        slightly more accurate.

    Returns
    -------
    list[Utterance] : sequential, non-overlapping utterances.

    Raises
    ------
    FileNotFoundError : if `audio_path` doesn't exist.
    TranscriptionError : if model loading or inference fails.
    """
    audio_path = Path(audio_path).resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    log.info(
        f"Loading Whisper model "
        f"[cyan]{model_size}[/cyan] on [cyan]{device}[/cyan] "
        f"([yellow]{compute_type}[/yellow])"
    )
    log.info(
        "[dim]First run downloads ~140 MB of weights — "
        "subsequent runs use the cache.[/dim]"
    )

    try:
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
    except Exception as e:
        raise TranscriptionError(
            f"Failed to load Whisper model '{model_size}': {e}"
        ) from e

    log.info(f"Transcribing [cyan]{audio_path.name}[/cyan]…")

    try:
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            # Helpful Whisper goodies:
            vad_filter=True,          # skip silence chunks
            vad_parameters=dict(min_silence_duration_ms=500),
        )
    except Exception as e:
        raise TranscriptionError(f"Whisper inference failed: {e}") from e

    detected_lang = info.language
    lang_prob = info.language_probability
    log.info(
        f"Detected language: [cyan]{detected_lang}[/cyan] "
        f"(confidence [yellow]{lang_prob:.0%}[/yellow])"
    )

    # `segments_iter` is a generator — materialize it into Utterance objects
    utterances: list[Utterance] = []
    for s in segments_iter:
        utterances.append(
            Utterance(
                start=round(s.start, 3),
                end=round(s.end, 3),
                text=s.text.strip(),
            )
        )

    if not utterances:
        log.warning(
            "[yellow]No speech detected in the audio. "
            "Is the file silent or too short?[/yellow]"
        )
    else:
        total_duration = utterances[-1].end
        log.info(
            f"[green]✓ Transcribed[/green] "
            f"[cyan]{len(utterances)}[/cyan] utterances "
            f"over [yellow]{total_duration:.1f}s[/yellow]"
        )

    return utterances