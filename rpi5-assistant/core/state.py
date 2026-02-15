"""
Shared application state with thread-safe access
"""

import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

# =============================================
# STATE ENUMS
# =============================================
class SystemState(Enum):
    """System operational states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    DETECTING = "detecting"
    ERROR = "error"

class EventType(Enum):
    """Types of events in the system"""
    BUTTON_PRESSED = "button_pressed"
    BUTTON_RELEASED = "button_released"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    STT_COMPLETE = "stt_complete"
    LLM_RESPONSE = "llm_response"
    VISION_RESULT = "vision_result"
    ERROR = "error"
    ANIMATION_FRAME = "animation_frame"

# =============================================
# EVENT DATACLASS
# =============================================
@dataclass
class Event:
    """Generic event structure"""
    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher priority events processed first

# =============================================
# SHARED STATE
# =============================================
class AppState:
    """Thread-safe shared application state"""
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # System state
        self.system_state = SystemState.IDLE
        self.error_message: Optional[str] = None
        
        # Button states (raw)
        self.button_k1_pressed = False
        self.button_k2_pressed = False
        self.button_k3_pressed = False
        
        # Audio state
        self.is_recording = False
        self.audio_data: Optional[bytes] = None
        self.recording_duration = 0.0
        
        # STT state
        self.transcribed_text: Optional[str] = None
        
        # LLM state
        self.llm_response: Optional[str] = None
        self.llm_thinking = False
        
        # Vision state
        self.detected_objects: List[Dict[str, Any]] = []
        self.last_image_path: Optional[str] = None
        
        # RAG state
        self.rag_context: Optional[str] = None
        
        # Animation state
        self.animation_frame = 0
        self.animation_running = True
        
        # Event queue
        self.event_queue: List[Event] = []
    
    # =============================================
    # THREAD-SAFE SETTERS
    # =============================================
    
    def set_system_state(self, state: SystemState) -> None:
        """Set system state (thread-safe)"""
        with self._lock:
            self.system_state = state
    
    def set_error(self, message: str) -> None:
        """Set error state (thread-safe)"""
        with self._lock:
            self.system_state = SystemState.ERROR
            self.error_message = message
    
    def clear_error(self) -> None:
        """Clear error state (thread-safe)"""
        with self._lock:
            if self.system_state == SystemState.ERROR:
                self.system_state = SystemState.IDLE
            self.error_message = None
    
    def set_button_state(self, button: str, pressed: bool) -> None:
        """Update button state (thread-safe)"""
        with self._lock:
            if button == "K1":
                self.button_k1_pressed = pressed
            elif button == "K2":
                self.button_k2_pressed = pressed
            elif button == "K3":
                self.button_k3_pressed = pressed
    
    def set_recording(self, recording: bool, duration: float = 0.0) -> None:
        """Update recording state (thread-safe)"""
        with self._lock:
            self.is_recording = recording
            self.recording_duration = duration
    
    def set_audio_data(self, data: bytes) -> None:
        """Set recorded audio data (thread-safe)"""
        with self._lock:
            self.audio_data = data
    
    def set_transcribed_text(self, text: str) -> None:
        """Set transcribed text (thread-safe)"""
        with self._lock:
            self.transcribed_text = text
    
    def set_llm_response(self, response: str) -> None:
        """Set LLM response (thread-safe)"""
        with self._lock:
            self.llm_response = response
            self.llm_thinking = False
    
    def set_llm_thinking(self, thinking: bool) -> None:
        """Set LLM thinking state (thread-safe)"""
        with self._lock:
            self.llm_thinking = thinking
    
    def set_detected_objects(self, objects: List[Dict[str, Any]]) -> None:
        """Set detected objects (thread-safe)"""
        with self._lock:
            self.detected_objects = objects
    
    def set_last_image_path(self, path: str) -> None:
        """Set last captured image path (thread-safe)"""
        with self._lock:
            self.last_image_path = path
    
    def set_rag_context(self, context: str) -> None:
        """Set RAG context (thread-safe)"""
        with self._lock:
            self.rag_context = context
    
    def set_animation_frame(self, frame: int) -> None:
        """Set animation frame (thread-safe)"""
        with self._lock:
            self.animation_frame = frame
    
    # =============================================
    # THREAD-SAFE GETTERS
    # =============================================
    
    def get_system_state(self) -> SystemState:
        """Get current system state (thread-safe)"""
        with self._lock:
            return self.system_state
    
    def get_button_state(self, button: str) -> bool:
        """Get button state (thread-safe)"""
        with self._lock:
            if button == "K1":
                return self.button_k1_pressed
            elif button == "K2":
                return self.button_k2_pressed
            elif button == "K3":
                return self.button_k3_pressed
            return False
    
    def get_audio_data(self) -> Optional[bytes]:
        """Get recorded audio data (thread-safe)"""
        with self._lock:
            return self.audio_data
    
    def get_transcribed_text(self) -> Optional[str]:
        """Get transcribed text (thread-safe)"""
        with self._lock:
            return self.transcribed_text
    
    def get_llm_response(self) -> Optional[str]:
        """Get LLM response (thread-safe)"""
        with self._lock:
            return self.llm_response
    
    def get_detected_objects(self) -> List[Dict[str, Any]]:
        """Get detected objects (thread-safe)"""
        with self._lock:
            return self.detected_objects.copy()
    
    def get_rag_context(self) -> Optional[str]:
        """Get RAG context (thread-safe)"""
        with self._lock:
            return self.rag_context
    
    def get_animation_frame(self) -> int:
        """Get animation frame (thread-safe)"""
        with self._lock:
            return self.animation_frame
    
    # =============================================
    # EVENT QUEUE
    # =============================================
    
    def enqueue_event(self, event: Event) -> None:
        """Add event to queue (thread-safe)"""
        with self._lock:
            self.event_queue.append(event)
            # Sort by priority (higher first)
            self.event_queue.sort(key=lambda e: -e.priority)
    
    def dequeue_event(self) -> Optional[Event]:
        """Remove and return next event (thread-safe)"""
        with self._lock:
            if self.event_queue:
                return self.event_queue.pop(0)
            return None
    
    def has_events(self) -> bool:
        """Check if events pending (thread-safe)"""
        with self._lock:
            return len(self.event_queue) > 0
    
    def clear_events(self) -> None:
        """Clear all pending events (thread-safe)"""
        with self._lock:
            self.event_queue.clear()


# =============================================
# GLOBAL STATE INSTANCE
# =============================================
app_state = AppState()
