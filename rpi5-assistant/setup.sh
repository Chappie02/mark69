#!/bin/bash
# Setup script for RPi5 Multimodal Assistant

set -e

echo "======================================"
echo "RPi5 Multimodal Assistant - Setup"
echo "======================================"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
MIN_VERSION="3.9"

if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
    echo -e "${RED}✗ Python 3.9+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}→ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo "Upgrading pip..."
pip install --quiet --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install requirements
echo "Installing dependencies (this may take 10-15 minutes)..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create model directories
mkdir -p models storage/images storage/vectordb
echo -e "${GREEN}✓ Directories created${NC}"

# Download models
echo ""
echo "======================================"
echo "Model Download"
echo "======================================"
echo ""
echo "Do you want to download the required models?"
echo "Note: This requires internet access"
echo ""
echo "Models to download:"
echo "  - Gemma 2B 4-bit GGUF (~2.2GB)"
echo "  - Whisper (auto-download on first run, ~141MB)"
echo "  - YOLO (auto-download on first run, ~6.2MB)"
echo ""
read -p "Download models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading models (Gemma GGUF, YOLO weights, Whisper, embeddings)..."
    # Use the Python downloader which attempts HF snapshot downloads when available
    python3 download_models.py || true
    echo -e "${GREEN}✓ Model download attempt finished${NC}"
else
    echo -e "${YELLOW}→ Skipping model download${NC}"
    echo "You can download manually later using:"
    echo "  python3 download_models.py"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "======================================"
echo ""
echo "To run the assistant:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
