import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.audio import extract_audio
from src.modules.transcribe import transcribe_audio
from src.modules.scenes import detect_scenes
from src.modules.segments import build_segments


def main():
    video_path = Path("data/sample.mp4")
    audio_path = Path(".cache/sample.wav")

    if not video_path.exists():
        print(f"Missing file: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print("Phase 3 — extract audio")
    print("=" * 60)
    extract_audio(video_path, audio_path)

    print("\n" + "=" * 60)
    print("Phase 4 — transcribe")
    print("=" * 60)
    utterances = transcribe_audio(
        audio_path,
        model_size="base",
        device="cpu",
        compute_type="int8",
    )

    print("\n" + "=" * 60)
    print("Phase 5 — detect scenes")
    print("=" * 60)
    scenes = detect_scenes(
        video_path,
        threshold=27.0,
        min_scene_length=5.0,
    )

    print("\n" + "=" * 60)
    print("Phase 6 — build segments")
    print("=" * 60)
    segments = build_segments(scenes, utterances)

    print(f"\nFinal result — {len(segments)} segments:\n")
    for seg in segments:
        preview = (
            seg.transcript[:80] + "..." if len(seg.transcript) > 80 else seg.transcript
        )
        preview = preview or "(silent)"
        print(f"  {seg}")
        print(f"    transcript: {preview}")
        print()


if __name__ == "__main__":
    main()
