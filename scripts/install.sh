#!/bin/bash
# Unified Narrato installation in virtual environment

set -e

echo "🎙️  Narrato - Complete Installation"
echo "===================================="
echo ""

# Create venv
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install base dependencies
echo "📥 Installing base dependencies..."
pip install -q python-docx gtts tqdm PyPDF2
echo "✓ Base dependencies installed"
echo ""

# Install Bark (optional but recommended)
echo "📥 Installing Bark TTS (high-quality local)..."
echo "   (This may take a few minutes...)"
pip install -q git+https://github.com/suno-ai/bark.git > /dev/null 2>&1 || {
    echo "⚠️  Bark installation skipped (optional)"
    echo "   You can still use gTTS engine"
}
echo "✓ Bark ready"
echo ""

echo "✅ Installation complete!"
echo ""
echo "🚀 Quick start:"
echo "   source venv/bin/activate"
echo "   python -m narrato document.docx"
echo "   python -m narrato document.docx --engine bark"
echo "   python gui_launcher.py"
