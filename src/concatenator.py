"""Concatenate MP3 files."""

import os
import shutil
import subprocess
import tempfile
from typing import List


def concatenate_audio(
    mp3_blobs: List[bytes],
    output_path: str,
    speed: float = 1.2,
) -> None:
    """
    Concatenate multiple MP3 byte blobs into a single MP3 file with speed adjustment.

    Uses ffmpeg with the concat demuxer and atempo filter for speed adjustment.
    Speed is applied during concatenation for efficiency.

    Args:
        mp3_blobs: List of MP3 byte blobs
        output_path: Path where the output MP3 should be written
        speed: Playback speed multiplier (1.0=normal, 1.2=20% faster, 0.75=25% slower)

    Raises:
        RuntimeError: If ffmpeg is not found or concatenation fails
    """
    # Check if ffmpeg is available
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed or not in PATH")

    if speed <= 0 or speed > 2.0:
        raise ValueError("Speed must be between 0.1 and 2.0")

    # Create temporary directory for chunk files and manifest
    temp_dir = tempfile.mkdtemp(prefix="docx2mp3_")

    try:
        # Generate a 300ms silence file to insert between chunks
        silence_path = os.path.join(temp_dir, "gap.mp3")
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "0.3", "-q:a", "9", silence_path
            ],
            capture_output=True,
            check=True
        )

        # Write each chunk to a temp file
        chunk_files = []
        for i, chunk_data in enumerate(mp3_blobs):
            chunk_path = os.path.join(temp_dir, f"chunk_{i:04d}.mp3")
            with open(chunk_path, "wb") as f:
                f.write(chunk_data)
            chunk_files.append(chunk_path)

        # Create ffmpeg concat manifest
        manifest_path = os.path.join(temp_dir, "manifest.txt")
        with open(manifest_path, "w") as f:
            for i, chunk_file in enumerate(chunk_files):
                f.write(f"file '{chunk_file}'\n")
                # Add silence gap between chunks, but not after the last one
                if i < len(chunk_files) - 1:
                    f.write(f"file '{silence_path}'\n")

        # Build ffmpeg command with atempo filter for speed adjustment
        audio_filter = f"atempo={speed}" if speed != 1.0 else "anull"

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", manifest_path,
            "-af", audio_filter,
            output_path,
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed: {result.stderr}"
            )

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
