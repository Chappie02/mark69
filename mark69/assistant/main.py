"""
Offline multimodal AI assistant — main entry.
Runs on Raspberry Pi 5: OLED eyes, push-to-talk, YOLOv8, local LLM.
All interaction is button-driven; no wake word, no cloud.
"""

import threading
import time

from . import audio
from . import buttons
from . import eyes
from . import llm
from . import stt
from . import tts
from . import vision
from .config import IMAGES_DIR
from .state_manager import State, StateManager


# Prompt for object explanation (K2)
OBJECT_PROMPT = 'Explain what a "{obj}" is and its common uses. Keep it to 1-3 short sentences.'


def main() -> None:
    state = StateManager()
    eye_display = eyes.EyeDisplay(state)
    eye_display.start()

    # Recording state for K1 hold
    record_stop = threading.Event()
    recording_done = threading.Event()
    recorded_wav: list = []  # [bytes] so worker can store result

    def k1_press() -> None:
        if not state.is_idle() and state.state != State.LISTENING:
            return
        state.set_state(State.LISTENING)
        eye_display.play_wakeup()
        record_stop.clear()
        recording_done.clear()
        recorded_wav.clear()

        def record_worker() -> None:
            wav = audio.record_while_pressed(record_stop)
            if wav:
                recorded_wav.append(wav)
            recording_done.set()

        threading.Thread(target=record_worker, daemon=True).start()

    def k1_release() -> None:
        record_stop.set()
        recording_done.wait(timeout=3.0)
        wav_bytes = recorded_wav[0] if recorded_wav else b""

        def process_worker() -> None:
            state.set_state(State.THINKING)
            text = stt.transcribe(wav_bytes)
            if not text.strip():
                state.set_state(State.ERROR)
                return
            response = llm.generate_full(text)
            if not response.strip():
                state.set_state(State.ERROR)
                return
            wav = tts.speak(response)
            if wav:
                audio.play_wav_bytes(wav)
            state.set_state(State.IDLE)

        if wav_bytes:
            threading.Thread(target=process_worker, daemon=True).start()
        else:
            state.set_state(State.IDLE)

    def k2_press() -> None:
        if not state.is_idle():
            return

        def detect_worker() -> None:
            state.set_state(State.DETECTING)
            img, labels = vision.capture_and_detect()
            if not labels:
                state.set_state(State.ERROR)
                tts_wav = tts.speak("I could not detect any object clearly.")
                if tts_wav:
                    audio.play_wav_bytes(tts_wav)
                return
            obj_name = labels[0]
            prompt = OBJECT_PROMPT.format(obj=obj_name)
            state.set_state(State.THINKING)
            response = llm.generate_full(prompt)
            if not response.strip():
                response = f"It's a {obj_name}."
            wav = tts.speak(response)
            if wav:
                audio.play_wav_bytes(wav)
            state.set_state(State.SUCCESS)

        threading.Thread(target=detect_worker, daemon=True).start()

    def k3_press() -> None:
        if not state.is_idle():
            return

        def capture_worker() -> None:
            img = vision.capture_image_as_array()
            path = vision.save_image(img, IMAGES_DIR, prefix="capture")
            eye_display.play_blink_capture()

        threading.Thread(target=capture_worker, daemon=True).start()

    btn = buttons.ButtonHandler(
        on_k1_press=k1_press,
        on_k1_release=k1_release,
        on_k2_press=k2_press,
        on_k3_press=k3_press,
    )
    btn.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        btn.stop()
        eye_display.stop()
        vision.stop_camera()


if __name__ == "__main__":
    main()
