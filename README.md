# Narrato: Convert Documents to Audio

A Python CLI and GUI tool that extracts text from `.docx` and `.pdf` files, chunks it intelligently, generates speech using pluggable engines (**gTTS**, **Bark**, **Gemini AI**, or **Kokoro**), and concatenates the resulting audio into a single smooth MP3.

## Features

- **Multiple Engines**: Choose between gTTS (fast), Bark (local), Gemini AI (cloud), or Kokoro (local/high-quality).
- **Kokoro TTS**: High-quality local voices with natural prosody (af_heart, am_adam, bf_emma, etc.).
- **Gemini AI Support**: Latest high-quality AI voices (Aoede, Charon, Fenrir, Kore, Puck).
- **Simple & free**: gTTS works immediately, no setup or downloads.
- **Fast & reliable**: Works immediately, no setup or downloads.
- **Smart chunking**: Respects sentence boundaries, avoiding mid-sentence cuts that create audible glitches.
- **Concurrent processing**: Uses threading to generate multiple chunks in parallel for faster conversion.
- **Lossless concatenation**: Uses ffmpeg to seamlessly stitch MP3 files with no quality loss.
- **Multiple languages**: Support for 100+ languages via gTTS.

## Installation

### Prerequisites

- Python 3.8 or higher
- ffmpeg (for MP3 concatenation)
- Internet connection (for gTTS and Gemini)

### Setup

```bash
# Navigate to the project directory
cd narrato

# Install Python dependencies
pip install -r requirements.txt

# Ensure ffmpeg is installed
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: choco install ffmpeg or download from https://ffmpeg.org

# (Optional) Set API Key for Gemini
export GEMINI_API_KEY="your_api_key_here"
```

## Usage

### Basic Usage

Convert a file to MP3 with default English narration (gTTS):

```bash
python -m src.cli report.docx
```

### Use Gemini Engine (Highest Quality)

```bash
python -m src.cli report.docx --engine gemini --voice Aoede
```

Voices: `Aoede`, `Charon`, `Fenrir`, `Kore`, `Puck`.
Requires `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable.

### Use Bark Engine (Local AI)

```bash
python -m src.cli report.docx --engine bark --voice en_speaker_0
```

### Use Kokoro Engine (Local High-Quality)

```bash
pip install kokoro soundfile
python -m src.cli report.docx --engine kokoro --voice af_heart
```

Voices: `af_heart`, `af_bella`, `af_nicole`, `am_adam`, `am_michael`, `bf_emma`, `bf_isabella`, `bm_george`, `bm_lewis`.

## Testing

### Test with a Short Document

1. Create a simple 1-page .docx file (or use an existing one)
2. Run: `python -m docx2mp3 test.docx`
3. Play `test.mp3` and verify it sounds correct

### Test with a Longer Document

1. Use a 20+ page .docx file
2. Run: `python -m docx2mp3 long_doc.docx`
3. Verify the output MP3 plays smoothly with no audible cuts or glitches at sentence boundaries

### Test Error Handling

```bash
# Test: Invalid file format
python -m docx2mp3 report.txt  # Should error: not .docx

# Test: Missing ffmpeg
# Temporarily hide ffmpeg from PATH and run the tool

# Test: Invalid language code
python -m docx2mp3 report.docx --voice xyz  # Should error
```

### Test Different Languages

Convert the same file in different languages:

```bash
python -m docx2mp3 report.docx -o english.mp3 --voice en
python -m docx2mp3 report.docx -o spanish.mp3 --voice es
python -m docx2mp3 report.docx -o french.mp3 --voice fr
python -m docx2mp3 report.docx -o german.mp3 --voice de
```

Listen to each to hear how the same content sounds in different languages.

## Architecture

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point, argument parsing, validation, orchestration |
| `extractor.py` | Extract text from .docx using python-docx |
| `chunker.py` | Intelligent text chunking respecting sentence boundaries |
| `tts_client.py` | Concurrent speech generation using Google TTS (gTTS) |
| `concatenator.py` | MP3 file concatenation via ffmpeg |

## Technical Details

### Chunking Algorithm

- Splits text on sentence boundaries (`.`, `!`, `?`)
- Uses greedy bin-packing to accumulate sentences up to 4096 characters
- If a single sentence exceeds 4096 characters, splits it at word boundaries
- Preserves document order exactly

### Speech Generation

- Uses Google Text-to-Speech (gTTS) via HTTP API
- Generates MP3 audio directly (24 kHz, mono)
- ThreadPoolExecutor runs multiple chunks in parallel
- Each worker makes independent API calls
- No local models needed, works immediately

### Audio Concatenation

- Writes each MP3 blob to a temporary file
- Uses ffmpeg concat demuxer with copy codec (no re-encoding)
- Lossless stitching: no quality loss at chunk boundaries
- Fast: avoids audio reprocessing

### Error Handling

- Validates input file exists and is .docx format
- Verifies ffmpeg is installed and on PATH
- Validates language code format (e.g., "en", "es", "fr")
- Cleans up temporary files on success or failure
- Handles gTTS API errors with meaningful messages

## Troubleshooting

### Error: "ffmpeg is not installed or not in PATH"

Install ffmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from https://ffmpeg.org or use `choco install ffmpeg`

### Error: "Input file must be .docx format"

Ensure your input file has a `.docx` extension and is a valid Word document.

### Error: "gTTS failed"

This usually means Google's API is unreachable. Check:
- Internet connection is working
- No proxy/firewall blocking Google APIs
- Try reducing workers: `--workers 2`

### Output MP3 is too quiet/too loud

You can post-process with ffmpeg:
```bash
ffmpeg -i input.mp3 -filter:a "volume=2.0" output.mp3  # Double volume
ffmpeg -i input.mp3 -filter:a "volume=0.5" output.mp3  # Halve volume
```

### Slow processing

- Reduce workers if internet is slow: `--workers 2`
- For faster processing with more bandwidth: `--workers 10`
- Large documents will naturally take longer

### Audio quality issues

- Try a different language: `--voice es`, `--voice fr`, etc.
- Ensure your .docx has proper punctuation and sentence structure
- For better results, see [CLAUDE.md](CLAUDE.md) for optional text preprocessing with Claude

### "Connection refused" or timeout errors

This can happen if:
- Google's API is temporarily unavailable
- Your internet connection is unstable
- You're hitting rate limits (try reducing workers)

Try again after waiting a moment.

## Limitations

- Currently does not extract text from tables (they are skipped)
- Maximum 4096 characters per chunk (API limit)
- Requires internet connection (uses Google's TTS API)
- Subject to Google's Terms of Service and rate limits
- gTTS uses 24 kHz mono audio (fixed quality)

## License

This tool is provided as-is for personal and commercial use.
