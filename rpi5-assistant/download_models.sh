#!/bin/bash
# Download all required models for rpi5-assistant
# Run this script from the rpi5-assistant directory
set -e

mkdir -p models
cd models

# Download LLM (Gemma)
echo "Downloading Gemma LLM..."
wget -O gemma.gguf "https://huggingface.co/google/gemma-2b-it-GGUF/resolve/main/gemma-2b-it-q4_K_M.gguf"

# Download YOLOv8n (nano)
echo "Downloading YOLOv8n..."
wget -O yolo.pt "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"

# Download Vosk STT model (small English)
echo "Downloading Vosk STT model..."
wget -O vosk-model-small-en-us-0.15.zip "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
unzip -o vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
rm -rf stt
mv vosk-model-small-en-us-0.15 stt

# Download Coqui TTS English model (optional, user may customize)
# See https://github.com/coqui-ai/TTS for more models
# Example: Download a small English model
# echo "Downloading Coqui TTS model..."
# mkdir -p tts
# wget -O tts/model.pth "https://huggingface.co/coqui/tts_models/en/ljspeech/tacotron2-DDC/resolve/main/model.pth"
# wget -O tts/config.json "https://huggingface.co/coqui/tts_models/en/ljspeech/tacotron2-DDC/resolve/main/config.json"

cd ..
echo "All models downloaded and placed in ./models/"
echo "For TTS, you may also use espeak-ng: sudo apt install espeak-ng"
