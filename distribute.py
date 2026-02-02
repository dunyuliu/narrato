#!/usr/bin/env python3
"""Package Narrato with virtual environment into a macOS .dmg file."""

import os
import shutil
import subprocess
import sys
import plistlib
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def run_command(cmd, description):
    """Run a command and show status."""
    print(f"  {description}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        print("✓")
        return True
    except subprocess.CalledProcessError as e:
        print("✗")
        print(f"    Error: {e.stderr}")
        return False


def should_exclude(path):
    """Check if path should be excluded from distribution."""
    exclude_patterns = [
        "__pycache__",
        ".pyc",
        ".pyo",
        ".egg-info",
        ".git",
        ".gitignore",
        "*.egg",
        ".pytest_cache",
        ".tox",
        "dist",
        "build",
        "*.dmg",
    ]

    path_str = str(path)
    for pattern in exclude_patterns:
        if pattern in path_str:
            return True
    return False


def copy_tree(src, dst, exclude_func=None):
    """Copy directory tree, excluding certain files."""
    os.makedirs(dst, exist_ok=True)

    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)

        if exclude_func and exclude_func(src_path):
            continue

        if os.path.isdir(src_path):
            copy_tree(src_path, dst_path, exclude_func)
        else:
            shutil.copy2(src_path, dst_path)


def create_app_bundle(dmg_staging, narrato_staging, icon_path=None):
    """Create a macOS .app bundle for easy launching."""
    app_path = dmg_staging / "Narrato.app"
    contents = app_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"

    # Create directories
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)

    # Copy icon if provided
    if icon_path and icon_path.exists():
        shutil.copy2(icon_path, resources / "AppIcon.icns")

    # Create launcher script with better error handling
    launcher = macos / "Narrato"
    launcher.write_text("""#!/bin/bash
# Narrato App Launcher
# This script activates the venv and launches the GUI

LOG_FILE="$HOME/.narrato_launch.log"

{
    echo "=== Narrato App Launch ==="
    echo "Time: $(date)"

    # Get the directory where this script is located (Contents/MacOS)
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    echo "Script dir: $SCRIPT_DIR"

    # Use relative path to find Narrato folder
    # Path structure: /Volumes/DMG/Narrato.app/Contents/MacOS/Narrato
    # We want: /Volumes/DMG/Narrato (sibling to Narrato.app)
    # From MacOS, go up 3 levels (MacOS->Contents->Narrato.app->DMG)
    cd "$SCRIPT_DIR/../../../Narrato" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Error: Could not navigate to Narrato folder"
        exit 1
    fi

    NARRATO_DIR="$(pwd)"
    echo "Narrato dir: $NARRATO_DIR"

    # Verify we're in the right place
    if [ ! -f "gui_launcher.py" ]; then
        echo "Error: gui_launcher.py not found"
        ls -la
        exit 1
    fi

    # Activate venv
    if [ ! -f "venv/bin/activate" ]; then
        echo "Error: venv not found"
        ls -la
        exit 1
    fi

    echo "Activating venv..."
    source venv/bin/activate
    echo "Venv activated, launching GUI..."

    # Launch GUI
    exec python gui_launcher.py

} >> "$LOG_FILE" 2>&1
""")
    launcher.chmod(0o755)

    # Create Info.plist
    plist_dict = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleExecutable": "Narrato",
        "CFBundleIdentifier": "com.narrato.app",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Narrato",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.0.1",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "10.14",
        "NSHighResolutionCapable": True,
    }

    # Add icon if it exists
    if (resources / "AppIcon.icns").exists():
        plist_dict["CFBundleIconFile"] = "AppIcon"

    plist_path = contents / "Info.plist"
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_dict, f)


def create_dmg_layout(temp_staging, dmg_staging, version, narrato_staging):
    """Create a nice DMG layout with background and drag-to-install."""
    # Copy icon to DMG root
    icon_file = Path(__file__).parent / "icon.png"
    if icon_file.exists():
        shutil.copy2(icon_file, dmg_staging / "icon.png")

    # Create the .app bundle
    create_app_bundle(dmg_staging, narrato_staging)

    # Create Applications symlink
    apps_link = dmg_staging / "Applications"
    if not apps_link.exists():
        os.symlink("/Applications", str(apps_link))

    # Create Install.command script
    install_script = dmg_staging / "INSTALL.command"
    install_script.write_text("""#!/bin/bash
# Narrato Installation Script

echo "======================================"
echo "Narrato v0.0.1 Installation"
echo "======================================"
echo ""

# Get the Narrato folder location
NARRATO_DIR=$(dirname "$0")/Narrato

if [ ! -d "$NARRATO_DIR" ]; then
    echo "❌ Narrato folder not found!"
    exit 1
fi

echo "✓ Found Narrato at: $NARRATO_DIR"
echo ""
echo "Next steps:"
echo "1. Open Terminal"
echo "2. Navigate to the Narrato folder: cd \"$NARRATO_DIR\""
echo "3. Activate the virtual environment: source venv/bin/activate"
echo "4. Launch the GUI: python gui_launcher.py"
echo ""
echo "Or use the CLI:"
echo "  python -m narrato document.docx"
echo "  python -m narrato document.pdf --engine bark"
echo ""
""")
    install_script.chmod(0o755)

    # Create a nicely formatted README for the DMG
    readme_path = dmg_staging / "README.txt"
    readme_path.write_text("""╔════════════════════════════════════════════════════════════╗
║  NARRATO v0.0.1 - Document to Speech Converter              ║
║  🎙️  Convert .docx and .pdf files to high-quality audio    ║
╚════════════════════════════════════════════════════════════╝

QUICK START
──────────
EASIEST:
1. Double-click "Narrato.app" to launch the GUI

ALTERNATIVE:
1. Drag the "Narrato" folder to Applications
2. Open Terminal and run:
   cd /Applications/Narrato
   source venv/bin/activate
   python gui_launcher.py

FEATURES
────────
✓ Convert .docx and .pdf to MP3 audio
✓ TTS Engines:
  • gTTS: Fast, 100+ languages, online
  • Bark: Best quality, 10 English speakers, local (Metal GPU on M-series Macs)
✓ Speed control (0.75x - 2.0x)
✓ Generate multiple speeds in one run
✓ CLI and GUI interfaces
✓ Metal GPU acceleration on Apple Silicon

COMMAND LINE USAGE
──────────────────
source venv/bin/activate

# Basic usage (gTTS)
python -m narrato document.docx

# Use Bark engine (best quality)
python -m narrato document.docx --engine bark --voice en_speaker_0

# Multiple speeds
python -m narrato document.docx --all-speeds

# Spanish narration with gTTS
python -m narrato document.docx --voice es

REQUIREMENTS
────────────
• Python 3.8+ (already included)
• macOS 10.14+ (M1/M2/M3 Macs support Metal GPU acceleration)
• Internet connection for gTTS

DOCUMENTATION
──────────────
• README.md - Full documentation
• QUICKSTART.txt - Quick reference
• docs/CLAUDE.md - Optional AI preprocessing
• docs/ARCHITECTURE.txt - Technical details

SUPPORT
───────
For issues: https://github.com/anthropics/claude-code
Or run: python -m narrato --help

Enjoy! 🎉
""")


def main():
    """Create .dmg distribution."""
    print("=" * 60)
    print("Narrato Distribution Builder")
    print("=" * 60)
    print()

    # Paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    temp_staging = Path("/tmp/narrato-staging")
    dmg_staging = temp_staging / "DMG"
    narrato_staging = dmg_staging / "Narrato"

    # Version
    version = "0.0.1"
    dmg_name = f"Narrato-v{version}.dmg"
    dmg_path = dist_dir / dmg_name

    print(f"Version: {version}")
    print(f"Output: {dmg_path}")
    print()

    # Clean up
    print("Preparing build environment...")
    if temp_staging.exists():
        print("  Cleaning previous staging...", end=" ", flush=True)
        shutil.rmtree(temp_staging)
        print("✓")

    if not dist_dir.exists():
        print("  Creating dist directory...", end=" ", flush=True)
        dist_dir.mkdir(exist_ok=True)
        print("✓")

    if dmg_path.exists():
        print("  Removing existing DMG...", end=" ", flush=True)
        os.remove(dmg_path)
        print("✓")

    print()
    print("Copying files...")

    # Copy narrato folder
    print("  Copying source code and venv...", end=" ", flush=True)
    copy_tree(str(project_root), str(narrato_staging), exclude_func=should_exclude)
    print("✓")

    # Create DMG layout
    print("  Creating DMG layout...", end=" ", flush=True)
    create_dmg_layout(temp_staging, dmg_staging, version, narrato_staging)
    print("✓")

    print()
    print("Creating macOS disk image (.dmg)...")

    # Create DMG
    hdiutil_cmd = (
        f'hdiutil create -volname "Narrato v{version}" '
        f'-srcfolder "{dmg_staging}" '
        f'-ov -format UDZO "{dmg_path}"'
    )

    if not run_command(hdiutil_cmd, "Building disk image"):
        print("\n✗ Failed to create DMG")
        return False

    print()
    print("=" * 60)
    print("✓ Distribution created successfully!")
    print("=" * 60)
    print()
    print(f"Output: {dmg_path}")
    print(f"Size: {dmg_path.stat().st_size / (1024**2):.1f} MB")
    print()
    print("DMG Contents:")
    print("  • Narrato.app - Double-clickable app bundle (GUI launcher)")
    print("  • Narrato/ - Main application folder with venv and source")
    print("  • Applications/ - Shortcut to macOS Applications folder")
    print("  • README.txt - Installation and usage instructions")
    print("  • INSTALL.command - Terminal installation helper")
    print()
    print("User Experience:")
    print("1. Double-click Narrato-v0.0.1.dmg to mount")
    print("2. Double-click Narrato.app to launch the GUI immediately")
    print("   OR drag 'Narrato' folder to Applications for CLI use")
    print()

    # Cleanup
    print("Cleaning up temporary files...")
    shutil.rmtree(temp_staging)
    print("✓ Done!")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
