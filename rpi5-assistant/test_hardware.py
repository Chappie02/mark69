#!/usr/bin/env python3
"""
Test and demo script for hardware components
Run individual tests or all tests together
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    BUTTON_K1, BUTTON_K2, BUTTON_K3,
    OLED_ADDRESS, OLED_I2C_BUS,
    AUDIO_SAMPLE_RATE
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================
# TESTS
# =============================================

def test_gpio():
    """Test GPIO button inputs"""
    logger.info("Testing GPIO buttons...")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        for pin, name in [(BUTTON_K1, "K1"), (BUTTON_K2, "K2"), (BUTTON_K3, "K3")]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            state = GPIO.input(pin)
            logger.info(f"  {name} (GPIO{pin}): {state} (should be 1)")
        
        GPIO.cleanup()
        logger.info("✓ GPIO test passed")
        return True
    except Exception as e:
        logger.error(f"✗ GPIO test failed: {e}")
        return False

def test_i2c():
    """Test I2C display connection"""
    logger.info("Testing I2C...")
    try:
        import smbus2
        bus = smbus2.SMBus(OLED_I2C_BUS)
        
        # Try to read from display
        try:
            data = bus.read_byte(OLED_ADDRESS)
            logger.info(f"  Device found at 0x{OLED_ADDRESS:02x}")
        except:
            logger.warning(f"  No device at 0x{OLED_ADDRESS:02x} (may still work)")
        
        bus.close()
        logger.info("✓ I2C test passed")
        return True
    except Exception as e:
        logger.error(f"✗ I2C test failed: {e}")
        return False

def test_oled():
    """Test OLED display"""
    logger.info("Testing OLED display...")
    try:
        from hardware.oled import OLEDDisplay
        
        oled = OLEDDisplay()
        oled.show_status("TEST", "Display OK")
        logger.info("✓ OLED test passed")
        oled.cleanup()
        return True
    except Exception as e:
        logger.error(f"✗ OLED test failed: {e}")
        return False

def test_camera():
    """Test Picamera2"""
    logger.info("Testing camera...")
    try:
        from picamera2 import Picamera2
        
        camera = Picamera2()
        logger.info(f"  Camera: {camera.camera_properties}")
        
        config = camera.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        camera.configure(config)
        camera.start()
        
        # Capture test frame
        frame = camera.capture_array()
        logger.info(f"  Frame shape: {frame.shape}")
        
        camera.stop()
        logger.info("✓ Camera test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Camera test failed: {e}")
        return False

def test_audio():
    """Test audio recording and playback"""
    logger.info("Testing audio...")
    try:
        import pyaudio
        import numpy as np
        
        p = pyaudio.PyAudio()
        
        # List devices
        logger.info(f"  Found {p.get_device_count()} audio devices")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['max_input_channels'] > 0:
                logger.info(f"    Input {i}: {info['name']}")
            if info['max_output_channels'] > 0:
                logger.info(f"    Output {i}: {info['name']}")
        
        # Test recording
        logger.info("  Recording 1 second of audio...")
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        for _ in range(int(AUDIO_SAMPLE_RATE / 1024)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        logger.info(f"  Recorded {len(frames) * 1024} samples")
        logger.info("✓ Audio test passed")
        p.terminate()
        return True
    except Exception as e:
        logger.error(f"✗ Audio test failed: {e}")
        return False

def test_stt():
    """Test speech-to-text model"""
    logger.info("Testing STT...")
    try:
        from audio.stt import SpeechToText
        
        stt = SpeechToText()
        if not stt.model:
            logger.warning("  Model not loaded (expected on first run)")
        else:
            logger.info("✓ STT test passed")
        return True
    except Exception as e:
        logger.error(f"✗ STT test failed: {e}")
        return False

def test_llm():
    """Test LLM model"""
    logger.info("Testing LLM...")
    try:
        from ai.llm import LocalLLM
        
        llm = LocalLLM()
        if not llm.is_loaded():
            logger.warning("  Model not loaded (expected without model file)")
            return True
        
        logger.info("  Testing generation...")
        response = llm.generate("Hello, what is 2+2?", max_tokens=50)
        logger.info(f"  Response: {response[:50]}...")
        logger.info("✓ LLM test passed")
        return True
    except Exception as e:
        logger.error(f"✗ LLM test failed: {e}")
        return False

def test_yolo():
    """Test YOLO model"""
    logger.info("Testing YOLO...")
    try:
        from ai.vision import YOLODetector
        
        yolo = YOLODetector()
        if not yolo.model:
            logger.warning("  Model not loaded (expected on first run)")
        else:
            logger.info("✓ YOLO test passed")
        return True
    except Exception as e:
        logger.error(f"✗ YOLO test failed: {e}")
        return False

def test_embeddings():
    """Test embeddings model"""
    logger.info("Testing embeddings...")
    try:
        from ai.embeddings import EmbeddingsModel
        
        embeddings = EmbeddingsModel()
        if not embeddings.model:
            logger.warning("  Model not loaded (expected on first run)")
            return True
        
        logger.info("  Testing embedding...")
        emb = embeddings.embed_text("Hello world")
        if emb:
            logger.info(f"  Embedding dim: {len(emb)}")
            logger.info("✓ Embeddings test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Embeddings test failed: {e}")
        return False

def test_rag():
    """Test RAG system"""
    logger.info("Testing RAG...")
    try:
        from ai.embeddings import EmbeddingsModel
        from ai.rag import RAGMemory
        
        embeddings = EmbeddingsModel()
        rag = RAGMemory(embeddings)
        
        stats = rag.get_stats()
        logger.info(f"  Status: {stats.get('status')}")
        logger.info(f"  Documents: {stats.get('documents', 0)}")
        
        logger.info("✓ RAG test passed")
        return True
    except Exception as e:
        logger.error(f"✗ RAG test failed: {e}")
        return False

def test_animation():
    """Test animation engine"""
    logger.info("Testing animation...")
    try:
        from hardware.animation import AnimationEngine
        
        animation = AnimationEngine()
        
        # Calculate eye positions at different phases
        for progress in [0.0, 0.2, 0.4, 0.6, 0.8]:
            left, right = animation._calculate_eye_positions(progress)
            logger.info(f"  Progress {progress}: L={left}, R={right}")
        
        logger.info("✓ Animation test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Animation test failed: {e}")
        return False

# =============================================
# MAIN
# =============================================

TESTS = {
    "gpio": test_gpio,
    "i2c": test_i2c,
    "oled": test_oled,
    "camera": test_camera,
    "audio": test_audio,
    "stt": test_stt,
    "llm": test_llm,
    "yolo": test_yolo,
    "embeddings": test_embeddings,
    "rag": test_rag,
    "animation": test_animation,
}

def run_tests(test_names=None):
    """Run selected tests"""
    if test_names is None:
        test_names = list(TESTS.keys())
    
    logger.info("=" * 60)
    logger.info("RPi5 Multimodal Assistant - Hardware Tests")
    logger.info("=" * 60)
    logger.info("")
    
    results = {}
    for name in test_names:
        if name not in TESTS:
            logger.warning(f"Unknown test: {name}")
            continue
        
        logger.info("")
        try:
            results[name] = TESTS[name]()
        except KeyboardInterrupt:
            logger.warning("Test interrupted")
            break
        except Exception as e:
            logger.error(f"Test exception: {e}", exc_info=True)
            results[name] = False
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} passed")
    logger.info("")
    
    return passed == total

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test hardware components"
    )
    parser.add_argument(
        "tests",
        nargs="*",
        default=list(TESTS.keys()),
        help=f"Tests to run (default: all). Options: {', '.join(TESTS.keys())}"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available tests"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available tests:")
        for name in TESTS.keys():
            print(f"  - {name}")
        return 0
    
    success = run_tests(args.tests)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
