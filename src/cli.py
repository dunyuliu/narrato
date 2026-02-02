"""CLI entry point for Narrato - document to audio conversion."""

import argparse
import os
import shutil
import sys
from pathlib import Path

from .extractor import extract_text
from .chunker import chunk_text
from .tts_client import text_to_speech
from .concatenator import concatenate_audio
from .engine import EngineFactory


def validate_inputs(args) -> None:
    """Validate input arguments and environment."""
    # Check input file exists and is supported format
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    supported_formats = (".docx", ".pdf")
    if not any(args.input.lower().endswith(fmt) for fmt in supported_formats):
        raise ValueError(
            f"Input file must be one of: {', '.join(supported_formats)}. "
            f"Got: {args.input}"
        )

    # Check ffmpeg is available
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is not installed or not in PATH. "
            "Please install ffmpeg to use this tool."
        )

    # Validate engine
    available_engines = EngineFactory.list_engines()
    if args.engine not in available_engines:
        raise ValueError(
            f"Invalid engine '{args.engine}'. "
            f"Available: {', '.join(available_engines)}"
        )

    # Validate voice/language for the chosen engine
    engine = EngineFactory.get_engine(args.engine)
    supported_voices = engine.get_supported_voices()
    if args.voice not in supported_voices:
        # If it's the default 'en' and we're using gemini, bark, or kokoro, pick a sensible default
        if args.voice == "en" and args.engine == "gemini":
            args.voice = "Aoede"
        elif args.voice == "en" and args.engine == "bark":
            args.voice = "en_speaker_0"
        elif args.voice == "en" and args.engine == "kokoro":
            args.voice = "af_heart"
        else:
            raise ValueError(
                f"Invalid voice '{args.voice}' for {engine.get_name()}. "
                f"Supported: {', '.join(supported_voices[:10])}... (and more)"
            )

    # Validate workers
    if args.workers < 1:
        raise ValueError("Number of workers must be at least 1")

    # Validate speed
    if args.speed < 0.1 or args.speed > 2.0:
        raise ValueError("Speed must be between 0.1 and 2.0")


def determine_output_path(input_path: str, output_arg: str = None) -> str:
    """Determine the output MP3 path."""
    if output_arg:
        return output_arg

    # Default: same name as input, but with .mp3 extension
    input_path = Path(input_path)
    return str(input_path.with_suffix(".mp3"))


def main():
    """Main CLI orchestrator."""
    parser = argparse.ArgumentParser(
        description="Narrato: Convert documents to lifelike audio with pluggable TTS engines",
    )
    parser.add_argument(
        "input",
        help="Path to input document (.docx or .pdf)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output MP3 file (default: same name with .mp3 extension)",
    )
    parser.add_argument(
        "--engine",
        default="gtts",
        choices=EngineFactory.list_engines(),
        help=f"TTS engine to use (default: gtts). Available: {', '.join(EngineFactory.list_engines())}",
    )
    parser.add_argument(
        "--voice",
        default="en",
        help="Language/voice code (default: en for gTTS). Try: es, fr, de, it, pt, ru, ja, zh-cn, etc.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent TTS generation threads (default: 1)",
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Speak slower (default: normal speed)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.2,
        help="Playback speed multiplier (default: 1.2, i.e., 20%% faster). 1.0=normal, 0.75=slower",
    )
    parser.add_argument(
        "--all-speeds",
        action="store_true",
        help="Generate 3 versions: 1.0x (normal), 1.2x (default), 1.5x (fast)",
    )

    args = parser.parse_args()

    try:
        # Validate inputs
        validate_inputs(args)

        # Determine output path
        output_path = determine_output_path(args.input, args.output)

        print(f"Extracting text from {args.input}...")
        text = extract_text(args.input)

        # Get chunk size from engine
        engine = EngineFactory.get_engine(args.engine)
        chunk_size = engine.get_chunk_size()

        print(f"Chunking text (size: {chunk_size})...")
        chunks = chunk_text(text, max_chunk_size=chunk_size)
        print(f"  {len(chunks)} chunks created")

        speed_label = "slow" if args.slow else "normal"
        print(f"Converting to speech (engine: {args.engine}, voice: {args.voice}, speed: {speed_label})...")
        mp3_blobs = text_to_speech(
            chunks,
            engine_name=args.engine,
            voice=args.voice,
            workers=args.workers,
            slow=args.slow,
        )

        # Generate audio(s)
        if args.all_speeds:
            # Generate 3 versions with different speeds
            speeds = [1.0, 1.2, 1.5]
            base_path = output_path.rsplit(".mp3", 1)[0] if output_path.endswith(".mp3") else output_path

            for speed in speeds:
                speed_output = f"{base_path}_{speed}x.mp3"
                print(f"Creating {speed}x version: {speed_output}...")
                concatenate_audio(mp3_blobs, speed_output, speed=speed)
                print(f"  ✓ {speed_output}")

            print(f"\n✓ Successfully created 3 versions:")
            for speed in speeds:
                speed_output = f"{base_path}_{speed}x.mp3"
                print(f"  - {speed_output}")
        else:
            # Generate single version with specified speed
            print(f"Concatenating audio to {output_path}...")
            concatenate_audio(mp3_blobs, output_path, speed=args.speed)
            print(f"✓ Successfully created {output_path}")

    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
