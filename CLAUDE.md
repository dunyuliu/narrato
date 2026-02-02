# Optional Claude Integration

This document explains how to optionally use Claude API to preprocess text before converting to speech. This is useful for:

- **Improving readability**: Fix formatting, capitalization, and punctuation
- **Enhancing clarity**: Expand abbreviations, clarify ambiguous passages
- **Customizing content**: Summarize sections, adjust tone, or restructure for better narration
- **Handling edge cases**: Clean up corrupted text, fix encoding issues

## Why Use Claude Preprocessing?

Piper TTS works best with well-formatted, clear text. Some .docx files may have:
- Inconsistent formatting or capitalization
- Abbreviations that should be expanded for clarity
- Awkward phrasing that sounds unnatural when spoken
- Mixed content (tables, footnotes) that needs cleanup

Claude can fix these issues automatically.

## Quick Start

### 1. Set Your Claude API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Get your key at: https://console.anthropic.com/account/keys

### 2. Create a Preprocessing Script

Create `preprocess.py` in your project:

```python
#!/usr/bin/env python3
"""Preprocess .docx text using Claude before TTS."""

import os
import sys
from anthropic import Anthropic
from narrato.extractor import extract_text

def preprocess_text_with_claude(text: str) -> str:
    """Use Claude to improve text for TTS narration."""
    client = Anthropic()

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""I'm converting this text to speech using AI narration.
Please improve it for better spoken narration:
- Fix capitalization and punctuation
- Expand abbreviations (e.g., "Dr." → "Doctor", "Inc." → "Incorporated")
- Clarify awkward phrasing
- Remove or simplify URLs and formatting marks
- Keep all content, just make it sound better when read aloud

Return ONLY the improved text, no explanations.

Text:
{text}"""
            }
        ]
    )

    return response.content[0].text

def main():
    """Preprocess a .docx file and save improved text."""
    if len(sys.argv) < 2:
        print("Usage: python preprocess.py input.docx [output.txt]")
        sys.exit(1)

    docx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "preprocessed.txt"

    print(f"Extracting text from {docx_path}...")
    text = extract_text(docx_path)

    print("Preprocessing with Claude...")
    improved_text = preprocess_text_with_claude(text)

    with open(output_path, "w") as f:
        f.write(improved_text)

    print(f"✓ Saved improved text to {output_path}")

if __name__ == "__main__":
    main()
```

### 3. Run Preprocessing

```bash
python preprocess.py my_document.docx preprocessed.txt
```

### 4. Convert Preprocessed Text Manually

The tool currently reads from .docx files. To use preprocessed text:

**Option A: Create a new .docx from preprocessed text**
```python
from docx import Document

doc = Document()
with open("preprocessed.txt", "r") as f:
    text = f.read()
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para)
doc.save("preprocessed.docx")
```

Then run: `python -m narrato preprocessed.docx`

**Option B: Extend narrato to support preprocessing**

See the section below for integrating Claude preprocessing directly into the tool.

## Advanced: Integrate Claude into narrato

To add Claude preprocessing as a built-in option:

### 1. Add Claude Support Module

Create `narrato/claude_preprocessor.py`:

```python
"""Optional Claude preprocessing for improved TTS quality."""

import os
from anthropic import Anthropic

def preprocess_text(text: str, instructions: str = None) -> str:
    """Preprocess text using Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Set this environment variable to use Claude preprocessing."
        )

    client = Anthropic()

    default_instructions = """I'm converting this text to speech.
Please improve it for better spoken narration:
- Fix capitalization and punctuation
- Expand abbreviations (e.g., "Dr." → "Doctor", "Inc." → "Incorporated")
- Clarify awkward phrasing
- Remove URLs and formatting marks
- Keep all content, just make it sound better when read aloud

Return ONLY the improved text, no explanations."""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""{instructions or default_instructions}

Text:
{text}"""
            }
        ]
    )

    return response.content[0].text
```

### 2. Update CLI to Support `--preprocess`

Edit `narrato/cli.py`, add argument:

```python
parser.add_argument(
    "--preprocess",
    action="store_true",
    help="Use Claude to preprocess text for better TTS quality",
)
```

### 3. Use Preprocessing in Main Flow

```python
from narrato.claude_preprocessor import preprocess_text

# In main():
if args.preprocess:
    print("Preprocessing text with Claude...")
    text = preprocess_text(text)
```

### 4. Usage

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python -m narrato document.docx --preprocess
```

## Cost Considerations

Claude API pricing (as of this writing):
- Input: ~$0.003 per 1K tokens
- Output: ~$0.015 per 1K tokens

For a 50,000-character document:
- ~12,500 tokens input (~$0.04)
- ~6,250 tokens output (~$0.09)
- **Total: ~$0.13 per document**

This is a one-time cost per document for preprocessing. Much cheaper than OpenAI's TTS API ($15/1M chars).

## Preprocessing Tips

### For Academic Papers
Ask Claude to:
- Expand acronyms in first use
- Simplify technical jargon
- Break up long, complex sentences

### For Fiction/Creative Writing
Ask Claude to:
- Preserve character voice and dialogue
- Enhance dramatic pauses
- Add scene descriptions for context

### For Technical Documentation
Ask Claude to:
- Convert code examples to descriptions
- Expand abbreviations
- Clarify steps and procedures

### Custom Instructions

Modify the prompt in the preprocessing function to match your needs:

```python
instructions = """Make this text sound like a friendly podcast host reading it.
Add natural pauses and enthusiasm where appropriate."""

improved = preprocess_text(text, instructions=instructions)
```

## Example Workflows

### Workflow 1: Quick One-Off Document

```bash
# Set up
export ANTHROPIC_API_KEY="sk-ant-..."

# Create preprocessing script
cat > preprocess.py << 'EOF'
# ... (see above)
EOF

# Preprocess
python preprocess.py my_document.docx > preprocessed.txt

# Convert to .docx and generate MP3
python << 'PYTHON'
from docx import Document
doc = Document()
with open("preprocessed.txt") as f:
    for para in f.read().split("\n\n"):
        if para.strip():
            doc.add_paragraph(para)
doc.save("preprocessed.docx")
PYTHON

python -m narrato preprocessed.docx
```

### Workflow 2: Batch Processing with Preprocessing

```bash
#!/bin/bash
for file in documents/*.docx; do
    echo "Processing $file..."
    python preprocess.py "$file" "temp.txt"
    # Create .docx from preprocessed text...
    python -m narrato preprocessed.docx -o "audio/$(basename $file .docx).mp3"
done
```

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not set"

Set your Claude API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Claude Preprocessing Too Slow

Claude preprocessing adds ~30-60 seconds per document depending on size. If this is too slow:
- Only preprocess problematic documents
- Preprocess in parallel with other tasks
- Use a faster/smaller Claude model (but quality may decrease)

### Text Changed More Than Expected

The prompt is flexible. You can customize it to be more conservative:

```python
instructions = """Only fix critical issues:
- Expand common abbreviations (Dr., Mr., etc.)
- Fix obvious typos
- Keep everything else as-is"""
```

### Integration with narrato Not Working

Make sure:
1. `ANTHROPIC_API_KEY` is set
2. `claude_preprocessor.py` is in the `narrato/` directory
3. CLI argument `--preprocess` is added correctly
4. Import statement is added to `cli.py`

## Summary

Claude preprocessing is **optional** and **recommended** for:
- Documents with poor formatting
- Text that contains abbreviations or jargon
- Any content that needs quality improvement for audio

For simple, well-formatted documents, preprocessing may not be necessary. The default Bark TTS quality is already quite good.

Choose preprocessing if you want to optimize for audio quality; skip it if you just want fast conversion to MP3.
