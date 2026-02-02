"""Generate speech from text chunks using pluggable TTS engines."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from tqdm import tqdm

from .engine import EngineFactory, TTSEngine


def text_to_speech(
    chunks: List[str],
    engine_name: str = "gtts",
    voice: str = "en",
    workers: int = 5,
    slow: bool = False,
    output_dir: str = None,
) -> List[bytes]:
    """
    Convert text chunks to speech using specified TTS engine.

    Calls are made concurrently using a ThreadPoolExecutor. Results are
    collected in order.

    Args:
        chunks: List of text chunks to convert
        engine_name: TTS engine to use ("gtts" or "bark")
        voice: Language/voice identifier (depends on engine)
        workers: Number of concurrent worker threads
        slow: If True, speak slower (supported by some engines)
        output_dir: Optional directory to save individual chunk files

    Returns:
        List of audio byte blobs in the same order as input chunks
    """
    # Get engine instance
    engine = EngineFactory.get_engine(engine_name)

    # Ensure output directory exists if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    audio_data = [None] * len(chunks)  # Preserve order

    def _generate_speech(index: int, chunk: str) -> tuple:
        """Generate speech for a single chunk."""
        try:
            # Call engine with appropriate parameters
            if engine_name == "gtts":
                # gTTS supports slow parameter
                audio_bytes = engine.synthesize(chunk, voice, slow=slow)
            else:
                # Other engines may not support slow
                audio_bytes = engine.synthesize(chunk, voice)
            return index, audio_bytes
        except Exception as e:
            raise RuntimeError(f"TTS failed for chunk {index}: {e}")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_generate_speech, i, chunk): i
            for i, chunk in enumerate(chunks)
        }

        # Use tqdm for progress bar
        for future in tqdm(
            as_completed(futures), total=len(chunks), desc="Generating speech"
        ):
            index, audio_bytes = future.result()
            audio_data[index] = audio_bytes

            # Save individual chunk if output_dir is specified
            if output_dir:
                chunk_filename = os.path.join(output_dir, f"chunk_{index:04d}.mp3")
                with open(chunk_filename, "wb") as f:
                    f.write(audio_bytes)

    return audio_data
