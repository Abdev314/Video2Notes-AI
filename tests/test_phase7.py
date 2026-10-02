import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

    # Full chain: phases 3 → 7
    extract_audio(video_path, audio_path)
    utterances = transcribe_audio(
        audio_path, model_size="base", device="cpu", compute_type="int8"
    )
    scenes = detect_scenes(video_path, threshold=27.0, min_scene_length=5.0)
    segments = build_segments(scenes, utterances)

    # The new part
    segments = extract_keyframes(
        video_path,
        segments,
        frames_dir,
        position="middle",
        quality=90,
        max_width=1280,
    )

    print(f"\n{len(segments)} segments with frames:\n")
    for seg in segments:
        print(f"  {seg}")
        print(f"    frame : {seg.frame_path}")
        print(f"    text  : {seg.transcript[:60]}...")
        print()


if __name__ == "__main__":
    main()
