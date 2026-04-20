"""
Segment — the core data object of the Video2Notes-AI pipeline.

"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Segment(BaseModel):
    """A single chapter of the lecture — the pipeline's unit of work."""
    model_config = {"extra": "allow"}   # ← add this line


    # --- Identity ---
    id: int = Field(..., description="1-based segment index", ge=1)

    # --- Time range (seconds from start of video) ---
    start_time: float = Field(..., description="Start in seconds", ge=0)
    end_time: float = Field(..., description="End in seconds", ge=0)

    # --- Content filled progressively by the pipeline ---
    transcript: str = Field(
        default="",
        description="All spoken text inside [start_time, end_time]",
    )
    frame_path: Optional[Path] = Field(
        default=None,
        description="Path to the keyframe JPEG for this segment",
    )

    # --- AI-generated fields (filled in Step 6) ---
    title: Optional[str] = Field(default=None, description="Chapter title")
    summary: Optional[str] = Field(default=None, description="2-3 sentence summary")
    key_points: list[str] = Field(
        default_factory=list, description="Main takeaways as bullet points"
    )

    # --- Validation ---
    @field_validator("end_time")
    @classmethod
    def _end_after_start(cls, v: float, info) -> float:
        start = info.data.get("start_time")
        if start is not None and v <= start:
            raise ValueError(
                f"end_time ({v}) must be greater than start_time ({start})"
            )
        return v

    # --- Convenience properties ---
    @property
    def duration(self) -> float:
        """Segment length in seconds."""
        return self.end_time - self.start_time

    @property
    def timestamp_label(self) -> str:
        """Human-readable range like '00:00:00 – 00:02:04'."""
        return f"{self._fmt(self.start_time)} – {self._fmt(self.end_time)}"

    @staticmethod
    def _fmt(seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def __str__(self) -> str:
        title = self.title or "(untitled)"
        return f"Segment #{self.id} [{self.timestamp_label}] — {title}"