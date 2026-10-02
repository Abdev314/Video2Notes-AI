import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.modules.transcribe import transcribe_audio


def main():
    audio_path = Path("output/sample.wav")

    if not audio_path.exists():
        print(f"Missing file: {audio_path}")
        sys.exit(1)

    print(f"Transcribing {audio_path}...")
    utterances = transcribe_audio(
        audio_path,
        model_size="base",
        language=None,
        device="cpu",
        compute_type="int8",
    )

    print(f"\nGot {len(utterances)} utterance(s):\n")
    for u in utterances:
        print(f"  [{u.start:.2f}s - {u.end:.2f}s] {u.text}")


if __name__ == "__main__":
    main()
