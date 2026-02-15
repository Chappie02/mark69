"""
Main controller orchestrating all subsystems
Processes button events and manages workflow
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime

from config import PROJECT_ROOT
from core.state import app_state, SystemState, EventType, Event
from hardware.buttons import ButtonManager
from hardware.oled import OLEDDisplay
from audio.recorder import AudioRecorder
from audio.stt import SpeechToText
from audio.tts import TextToSpeech
from ai.llm import LocalLLM
from ai.vision import YOLODetector
from ai.rag import RAGMemory
from ai.embeddings import EmbeddingsModel

# =============================================
# LOGGER SETUP
# =============================================
logger = logging.getLogger(__name__)

# =============================================
# CONTROLLER
# =============================================
class Controller:
    """Main application controller"""
    
    def __init__(self):
        """Initialize all subsystems"""
        logger.info("Initializing Controller...")
        
        # Hardware
        self.button_manager: Optional[ButtonManager] = None
        self.oled: Optional[OLEDDisplay] = None
        
        # Audio
        self.recorder: Optional[AudioRecorder] = None
        self.stt: Optional[SpeechToText] = None
        self.tts: Optional[TextToSpeech] = None
        
        # AI
        self.llm: Optional[LocalLLM] = None
        self.yolo: Optional[YOLODetector] = None
        self.rag: Optional[RAGMemory] = None
        self.embeddings: Optional[EmbeddingsModel] = None
        
        # State
        self._running = False
    
    def initialize(self) -> bool:
        """Initialize all subsystems. Returns True on success."""
        try:
            logger.info("Starting subsystem initialization...")
            
            # 1. Initialize embeddings model (needed by RAG)
            logger.info("Loading embeddings model...")
            self.embeddings = EmbeddingsModel()
            
            # 2. Initialize RAG
            logger.info("Initializing RAG memory system...")
            self.rag = RAGMemory(self.embeddings)
            
            # 3. Initialize LLM
            logger.info("Loading LLM model...")
            self.llm = LocalLLM()
            if not self.llm.is_loaded():
                logger.error("Failed to load LLM model")
                return False
            
            # 4. Initialize Vision
            logger.info("Loading YOLO model...")
            self.yolo = YOLODetector()
            
            # 5. Initialize Audio
            logger.info("Initializing audio system...")
            self.recorder = AudioRecorder()
            self.stt = SpeechToText()
            self.tts = TextToSpeech()
            
            # 6. Initialize Hardware
            logger.info("Initializing hardware (buttons, OLED)...")
            try:
                self.button_manager = ButtonManager(self._on_button_event)
            except Exception as e:
                logger.warning(f"Button manager failed: {e}. Continuing without buttons.")
                self.button_manager = None
            
            try:
                self.oled = OLEDDisplay()
            except Exception as e:
                logger.warning(f"OLED initialization failed: {e}. Continuing without display.")
                self.oled = None
            
            logger.info("✓ All subsystems initialized successfully!")
            self._running = True
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            app_state.set_error(f"Initialization failed: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Gracefully shutdown all subsystems"""
        logger.info("Shutting down controller...")
        self._running = False
        
        # Stop animation
        app_state.animation_running = False
        
        # Shutdown hardware
        if self.button_manager:
            self.button_manager.stop()
        if self.oled:
            self.oled.cleanup()
        
        # Shutdown audio
        if self.recorder:
            self.recorder.stop_recording()
        
        # Shutdown AI
        if self.llm:
            self.llm.cleanup()
        
        logger.info("✓ Shutdown complete")
    
    # =============================================
    # BUTTON EVENT HANDLERS
    # =============================================
    
    def _on_button_event(self, button: str, pressed: bool) -> None:
        """Handle button events from button manager"""
        if pressed:
            if button == "K1":
                logger.info("K1 pressed: Starting push-to-talk")
                self._start_push_to_talk()
            elif button == "K2":
                logger.info("K2 pressed: Starting object detection")
                self._handle_object_detection()
            elif button == "K3":
                logger.info("K3 pressed: Capturing image")
                self._handle_image_capture()
        else:
            if button == "K1":
                logger.info("K1 released: Stopping push-to-talk")
                self._stop_push_to_talk()
    
    # =============================================
    # K1 - PUSH TO TALK
    # =============================================
    
    def _start_push_to_talk(self) -> None:
        """K1 pressed: Start recording"""
        if app_state.get_system_state() == SystemState.LISTENING:
            logger.warning("Already listening, ignoring duplicate K1 press")
            return
        
        app_state.set_system_state(SystemState.LISTENING)
        if self.oled:
            self.oled.show_status("LISTENING...", "🎤 Recording")
        
        if self.recorder:
            self.recorder.start_recording()
        logger.info("Recording started")
    
    def _stop_push_to_talk(self) -> None:
        """K1 released: Stop recording and process"""
        if app_state.get_system_state() != SystemState.LISTENING:
            return
        
        if self.recorder:
            audio_data = self.recorder.stop_recording()
            if audio_data:
                app_state.set_audio_data(audio_data)
                logger.info(f"Recording stopped. Audio size: {len(audio_data)} bytes")
                
                # Process async
                self._process_push_to_talk_async(audio_data)
            else:
                logger.warning("No audio data recorded")
                app_state.set_system_state(SystemState.IDLE)
    
    def _process_push_to_talk_async(self, audio_data: bytes) -> None:
        """Process push-to-talk (non-blocking)"""
        try:
            # Update state
            app_state.set_system_state(SystemState.PROCESSING)
            if self.oled:
                self.oled.show_status("PROCESSING", "🔄 Converting speech...")
            
            # 1. Speech-to-Text
            logger.info("Converting speech to text...")
            if self.stt:
                text = self.stt.transcribe(audio_data)
                if text:
                    logger.info(f"Transcribed: {text}")
                    app_state.set_transcribed_text(text)
                else:
                    logger.warning("STT returned empty")
                    app_state.set_system_state(SystemState.IDLE)
                    return
            
            # 2. Query RAG for context
            logger.info("Retrieving context from memory...")
            if self.rag:
                context = self.rag.query(text, top_k=3)
                app_state.set_rag_context(context)
                logger.info(f"RAG context retrieved: {len(context)} chars")
            
            # 3. Generate LLM response
            app_state.set_system_state(SystemState.RESPONDING)
            if self.oled:
                self.oled.show_status("THINKING", "🧠 Generating response...")
            
            logger.info("Generating LLM response...")
            if self.llm:
                response = self.llm.generate(text, context)
                app_state.set_llm_response(response)
                logger.info(f"LLM response: {response[:100]}...")
                
                # 4. Store in RAG for future reference
                if self.rag:
                    self.rag.store(f"User: {text}\nAssistant: {response}")
                    logger.info("Stored interaction in memory")
            
            # 5. Text-to-Speech
            if self.oled:
                self.oled.show_status("SPEAKING", "🔊 Playing response...")
            
            logger.info("Converting response to speech...")
            if self.tts:
                self.tts.speak(response)
                logger.info("Speech playback complete")
            
            # Done
            app_state.set_system_state(SystemState.IDLE)
            if self.oled:
                self.oled.show_status("READY", "👁️  Watching...")
            
        except Exception as e:
            logger.error(f"Push-to-talk processing failed: {e}", exc_info=True)
            app_state.set_error(f"STT/LLM error: {str(e)}")
            if self.oled:
                self.oled.show_status("ERROR", str(e)[:20])
    
    # =============================================
    # K2 - OBJECT DETECTION
    # =============================================
    
    def _handle_object_detection(self) -> None:
        """K2 pressed: Capture and detect objects"""
        if app_state.get_system_state() in [SystemState.LISTENING, SystemState.PROCESSING, SystemState.RESPONDING]:
            logger.warning("System busy, ignoring K2")
            return
        
        try:
            app_state.set_system_state(SystemState.DETECTING)
            if self.oled:
                self.oled.show_status("DETECTING", "📸 Capturing...")
            
            # Capture image
            if self.yolo:
                logger.info("Capturing image for detection...")
                image_path = self.yolo.capture_image()
                if not image_path:
                    logger.error("Failed to capture image")
                    app_state.set_system_state(SystemState.IDLE)
                    return
                
                app_state.set_last_image_path(image_path)
                logger.info(f"Image captured: {image_path}")
                
                # Run detection
                if self.oled:
                    self.oled.show_status("DETECTING", "🤖 Analyzing...")
                
                logger.info("Running YOLO inference...")
                detections = self.yolo.detect(image_path)
                
                if detections:
                    logger.info(f"Detected {len(detections)} objects")
                    app_state.set_detected_objects(detections)
                    
                    # Store in RAG
                    if self.rag:
                        detection_summary = self.yolo.get_detection_summary(image_path, detections)
                        self.rag.store(detection_summary)
                        logger.info("Stored detection in memory")
                    
                    # Generate explanation
                    if self.oled:
                        self.oled.show_status("EXPLAINING", "💭 Generating...")
                    
                    if self.llm:
                        explanation = self.llm.explain_detections(detections)
                        logger.info(f"Explanation: {explanation[:100]}...")
                        
                        if self.tts:
                            self.tts.speak(explanation)
                else:
                    logger.warning("No objects detected")
                    if self.tts:
                        self.tts.speak("No objects detected in the scene.")
            
            app_state.set_system_state(SystemState.IDLE)
            if self.oled:
                self.oled.show_status("READY", "👁️  Watching...")
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}", exc_info=True)
            app_state.set_error(f"Detection error: {str(e)}")
            if self.oled:
                self.oled.show_status("ERROR", str(e)[:20])
    
    # =============================================
    # K3 - IMAGE CAPTURE ONLY
    # =============================================
    
    def _handle_image_capture(self) -> None:
        """K3 pressed: Capture and save image"""
        try:
            app_state.set_system_state(SystemState.PROCESSING)
            if self.oled:
                self.oled.show_status("CAPTURING", "📷 Saving...")
            
            if self.yolo:
                logger.info("Capturing image for storage...")
                image_path = self.yolo.capture_image()
                if image_path:
                    app_state.set_last_image_path(image_path)
                    logger.info(f"Image saved: {image_path}")
                    
                    if self.tts:
                        self.tts.speak("Image captured and saved.")
                else:
                    logger.error("Failed to capture image")
                    if self.tts:
                        self.tts.speak("Failed to capture image.")
            
            app_state.set_system_state(SystemState.IDLE)
            if self.oled:
                self.oled.show_status("READY", "👁️  Watching...")
            
        except Exception as e:
            logger.error(f"Image capture failed: {e}", exc_info=True)
            app_state.set_error(f"Capture error: {str(e)}")
            if self.oled:
                self.oled.show_status("ERROR", str(e)[:20])
    
    # =============================================
    # EVENT LOOP
    # =============================================
    
    def run_event_loop(self) -> None:
        """Non-blocking event loop (called from main)"""
        try:
            # Process any pending events
            while app_state.has_events():
                event = app_state.dequeue_event()
                if event:
                    logger.debug(f"Processing event: {event.type}")
                    # Events can be processed here if needed
            
        except Exception as e:
            logger.error(f"Event loop error: {e}", exc_info=True)
