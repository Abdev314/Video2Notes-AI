import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.ai import analyze_segments
from src.modules.audio import extract_audio
from src.modules.export import export_markdown
from src.modules.keyframes import extract_keyframes
from src.modules.scenes import detect_scenes
from src.modules.segments import build_segments
from src.modules.transcribe import transcribe_audio


def main():
    video_path = Path("data/sample.mp4")
    audio_path = Path(".cache/sample.wav")
    frames_dir = Path("output/frames")
    notes_path = Path("output/notes.md")

    if not video_path.exists():
        print(f"Missing: {video_path}")
        sys.exit(1)

    # Full pipeline — all 7 steps
    extract_audio(video_path, audio_path)
    utterances = transcribe_audio(audio_path, model_size="base")
    scenes = detect_scenes(video_path, threshold=27.0, min_scene_length=5.0)
    segments = build_segments(scenes, utterances)
    segments = extract_keyframes(video_path, segments, frames_dir)
    segments = analyze_segments(segments, model="llama3.1:8b")

    # The final step
    export_markdown(
        segments,
        notes_path,
        title="Redis in 100 Seconds — Notes",
        subtitle="Auto-generated lecture notes",
        embed_frames=True,
        include_transcript=False,
    )

    print(f"\n✅ All done. Open: {notes_path}")


if __name__ == "__main__":
    main()
