import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.scenes import detect_scenes


def main():
    video_path = Path("data/sample.mp4")

    if not video_path.exists():
        print(f"Missing file: {video_path}")
        print("Put any video with visual changes at data/sample.mp4")
        sys.exit(1)

    print(f"Detecting scenes in {video_path}...")
    scenes = detect_scenes(
        video_path,
        threshold=27.0,
        min_scene_length=5.0,  # low for short test videos
    )

    print(f"\nFound {len(scenes)} scene(s):\n")
    for i, (start, end) in enumerate(scenes, 1):
        duration = end - start
        print(f"  Scene {i}: {start:6.2f}s - {end:6.2f}s  ({duration:.2f}s)")


if __name__ == "__main__":
    main()
