#!/usr/bin/env python3
"""
Fully offline multimodal robotic AI assistant.
Raspberry Pi 5, 4GB. Button-driven; state machine; animation never blocks.
"""

import queue
import threading
import time

from assistant.config import IMAGES_DIR
from assistant.core.event_bus import EventBus, Event
from assistant.core.state_manager import State, StateManager
from assistant.hardware.buttons import ButtonManager
from assistant.hardware.display import Display
from assistant.hardware.eyes import EyeAnimationController
from assistant.hardware.camera import Camera
from assistant.audio.recorder import AudioRecorder
from assistant.audio.stt import STTEngine
from assistant.audio.tts import TTSEngine
from assistant.ai.llm import LLMEngine
from assistant.ai.vision import VisionEngine
from assistant.utils.image_saver import save_capture


# System prompt for assistant personality
SYSTEM_PROMPT = (
    "You are a friendly robotic assistant running on a Raspberry Pi. "
    "Give short, clear answers. Be helpful and concise."
)


def run():
    event_bus = EventBus()
    state_manager = StateManager(event_bus)
    display = Display()
    display.init()
    eyes = EyeAnimationController(display, state_manager, event_bus)
    eyes.start()

    buttons = ButtonManager(event_bus)
    buttons.start()

    recorder = AudioRecorder()
    stt = STTEngine()
    tts = TTSEngine()
    llm = LLMEngine()
    vision = VisionEngine()
    camera = Camera()

    # Processing queue: (action, payload)
    work_queue: queue.Queue = queue.Queue()
    recording_thread_ref: list = []  # [Thread] so both handlers see same ref

    def on_k1_pressed(_: dict) -> None:
        state_manager.set_state(State.LISTENING)
        recorder.start()
        t = threading.Thread(target=recorder.run_capture_loop, daemon=True)
        recording_thread_ref.clear()
        recording_thread_ref.append(t)
        t.start()

    def on_k1_released(_: dict) -> None:
        audio = recorder.stop()
        if recording_thread_ref:
            recording_thread_ref[0].join(timeout=1.0)
            recording_thread_ref.clear()
        work_queue.put(("ptt", {"audio": audio}))

    def on_k2_pressed(_: dict) -> None:
        work_queue.put(("detect", {}))

    def on_k3_pressed(_: dict) -> None:
        work_queue.put(("capture", {}))

    event_bus.subscribe(Event.K1_PRESSED, on_k1_pressed)
    event_bus.subscribe(Event.K1_RELEASED, on_k1_released)
    event_bus.subscribe(Event.K2_PRESSED, on_k2_pressed)
    event_bus.subscribe(Event.K3_PRESSED, on_k3_pressed)

    def processing_worker() -> None:
        while True:
            try:
                action, payload = work_queue.get()
                if action == "ptt":
                    _do_ptt(payload, state_manager, stt, llm, tts)
                elif action == "detect":
                    _do_detect(state_manager, camera, vision, llm, tts)
                elif action == "capture":
                    _do_capture(state_manager, camera, eyes)
            except Exception:
                state_manager.set_state(State.ERROR)
                time.sleep(1.0)
                state_manager.set_state(State.IDLE)

    def _do_ptt(
        payload: dict,
        sm: StateManager,
        stt_engine: STTEngine,
        llm_engine: LLMEngine,
        tts_engine: TTSEngine,
    ) -> None:
        audio = payload.get("audio")
        sm.set_state(State.THINKING)
        text = stt_engine.transcribe(audio) if audio else ""
        if not text.strip():
            tts_engine.speak("I didn't catch that. Try again.")
            sm.set_state(State.IDLE)
            return
        response_parts = []
        for token in llm_engine.generate(text, system_prompt=SYSTEM_PROMPT, stream=True):
            response_parts.append(token)
        response = "".join(response_parts).strip()
        if not response:
            response = "I'm not sure how to answer that."
        sm.set_state(State.SPEAKING)
        tts_engine.speak(response)
        sm.set_state(State.IDLE)

    def _do_detect(
        sm: StateManager,
        cam: Camera,
        vis: VisionEngine,
        llm_engine: LLMEngine,
        tts_engine: TTSEngine,
    ) -> None:
        sm.set_state(State.DETECTING)
        img = cam.capture()
        if img is None:
            sm.set_state(State.ERROR)
            tts_engine.speak("Camera error.")
            time.sleep(1.0)
            sm.set_state(State.IDLE)
            return
        label = vis.detect_top(img)
        if label is None:
            sm.set_state(State.ERROR)
            tts_engine.speak("I didn't detect any object. Try again.")
            time.sleep(1.0)
            sm.set_state(State.IDLE)
            return
        sm.set_state(State.THINKING)
        prompt = f"Explain what a {label} is and its common uses in one short paragraph."
        response_parts = []
        for token in llm_engine.generate(prompt, system_prompt=SYSTEM_PROMPT, stream=True):
            response_parts.append(token)
        response = "".join(response_parts).strip() or f"A {label} is an object."
        sm.set_state(State.SPEAKING)
        tts_engine.speak(response)
        sm.set_state(State.SUCCESS)
        eyes.trigger_success()
        time.sleep(1.0)
        sm.set_state(State.IDLE)

    def _do_capture(sm: StateManager, cam: Camera, eyes_ctrl: EyeAnimationController) -> None:
        img = cam.capture()
        if img is not None:
            try:
                save_capture(img)
                eyes_ctrl.trigger_capture_blink()
            except Exception:
                pass
        sm.set_state(State.IDLE)

    proc_thread = threading.Thread(target=processing_worker, daemon=True)
    proc_thread.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        buttons.stop()
        eyes.stop()
        recorder.close()
        camera.close()


if __name__ == "__main__":
    run()
