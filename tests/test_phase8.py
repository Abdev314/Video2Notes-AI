import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.ai import analyze_segments
from src.modules.audio import extract_audio
from src.modules.keyframes import extract_keyframes
from src.modules.scenes import detect_scenes
from src.modules.segments import build_segments
from src.modules.transcribe import transcribe_audio


def main():
    video_path = Path("data/sample.mp4")
    audio_path = Path(".cache/sample.wav")
    frames_dir = Path("output/frames")

    if not video_path.exists():
        print(f"Missing: {video_path}")
        sys.exit(1)

    # Full pipeline so far
    extract_audio(video_path, audio_path)
    utterances = transcribe_audio(audio_path, model_size="base")
    scenes = detect_scenes(video_path, threshold=27.0, min_scene_length=5.0)
    segments = build_segments(scenes, utterances)
    segments = extract_keyframes(video_path, segments, frames_dir)

    # The new part
    segments = analyze_segments(
        segments,
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        temperature=0.3,
        max_retries=2,
    )

    print(f"\n{len(segments)} analyzed segments:\n")
    for seg in segments:
        print(f"=== Segment #{seg.id} [{seg.timestamp_label}] ===")
        print(f"  Title    : {seg.title or '(skipped)'}")
        if seg.summary:
            print(f"  Summary  : {seg.summary}")
        if seg.key_points:
            print("  Key points:")
            for kp in seg.key_points:
                print(f"    - {kp}")
        print()


if __name__ == "__main__":
    main()
