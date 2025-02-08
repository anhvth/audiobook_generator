import os
import time
from dataclasses import dataclass
from pathlib import Path
import io
import pyperclip
import soundfile as sf
from kokoro import KPipeline

# pydub + simpleaudio-based playback (allows stopping audio)
from pydub import AudioSegment
import threading
from playsound import playsound
from loguru import logger


class PlaySoundInThread:
    """
    Plays a sound file (via pydub + simpleaudio) in a separate thread
    and allows interruption (stop) of the currently playing audio.
    """

    def __init__(self):
        self.playing = False
        self.current_thread = None
        self.play_obj = None  # Will hold the simpleaudio.PlayObject

    def play(self, sound_file):
        """Play sound file in a separate thread, stopping any previously playing audio."""
        # If audio is already playing, interrupt it first
        if self.playing:
            self.interrupt()

        def _play():
            self.playing = True
            try:
                playsound(sound_file)
            finally:
                self.playing = False
                self.play_obj = None

        def _check_to_interrupt():
            # this track the changes of clipboard, if the clipboard is changed, then interrupt the current playing sound
            v = pyperclip.paste().strip()
            while self.playing:
                current_text = pyperclip.paste().strip()
                if current_text != v:
                    self.interrupt()
                    logger.info("Interrupted by clipboard change.")
                    break
                time.sleep(0.1)

        self.current_thread = threading.Thread(target=_play, daemon=True)
        self.current_thread.start()

        self.thread_check = threading.Thread(target=_check_to_interrupt, daemon=True)
        self.thread_check.start()

    def interrupt(self):
        """Stop currently playing sound immediately."""
        self.playing = False
        # If there's an active playback object, stop it now.
        if self.play_obj is not None and self.play_obj.is_playing():
            self.play_obj.stop()
        # Optionally, wait briefly for the thread to wrap up
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=0.1)
        if hasattr(self, "thread_check") and self.thread_check and self.thread_check.is_alive():
            self.thread_check.join(timeout=0.1)


sound_player = PlaySoundInThread()


@dataclass
class Config:
    LANG_CODE: str = (
        "a"  # 🇺🇸 'a'=American, 🇬🇧 'b'=British, 🇯🇵 'j'=Japanese, 🇨🇳 'z'=Chinese
    )
    VOICE: str = "af_heart"
    SPEED: float = 1.0
    SAMPLE_RATE: int = 24000
    OUTPUT_FILE: str = "sound.wav"
    POLLING_INTERVAL: float = 0.01
    MAX_TEXT_LENGTH: int = 100


class TextToSpeechManager:
    def __init__(self, config: Config):
        self.config = config
        self.pipeline = KPipeline(lang_code=config.LANG_CODE)
        self.latest_text = ""

    def text_to_speech(self, text: str) -> None:
        """Convert text to speech and play it."""
        if not text:
            return
        try:
            # split the text into chunks each one less than MAX_TEXT_LENGTH words
            # texts = [text[i : i + self.config.MAX_TEXT_LENGTH] for i in range(0, len(text), self.config.MAX_TEXT_LENGTH)]
            # splilt by ".\n"
            # texts = text.split(".\n")
            # for text in texts:
            logger.info(f"Converting: {text}")
            text = text.replace('\n', ' ')
            generator = self.pipeline(
                text,
                voice=self.config.VOICE,
                speed=self.config.SPEED,
                split_pattern=r"\.\n+",
            )

            # We only grab the first generated audio chunk in this example
            for _, _, audio in generator:
                while sound_player.playing:
                    time.sleep(0.5)
                self._save_and_play_audio(audio)

        except Exception as e:
            logger.info(f"Error in text to speech conversion: {e}")

    def _save_and_play_audio(self, audio) -> None:
        """Save the audio to file, then play it via our threaded player."""
        try:
            buffer = io.BytesIO()
            # Save to WAV in memory
            sf.write(buffer, audio, self.config.SAMPLE_RATE, format="WAV")
            buffer.seek(0)

            output_path = Path(self.config.OUTPUT_FILE)
            # Write the buffer to disk
            output_path.write_bytes(buffer.getvalue())

            # Play the file via our custom thread-based sound_player
            sound_player.play(str(output_path))

        except Exception as e:
            logger.info(f"Error in audio processing: {e}")

    def monitor_clipboard(self) -> None:
        """Continuously monitor the clipboard for changes, convert to speech."""
        logger.info("Monitoring clipboard... Press Ctrl+C to stop.")
        try:
            while True:
                current_text = pyperclip.paste().strip()
                # Truncate to MAX_TEXT_LENGTH words
                # words = current_text.split()[: self.config.MAX_TEXT_LENGTH]
                # current_text = " ".join(words)

                if current_text and current_text != self.latest_text:
                    # Interrupt any current playback before playing new text
                    sound_player.interrupt()
                    self.latest_text = current_text
                    self.text_to_speech(current_text)

                time.sleep(self.config.POLLING_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Stopping clipboard monitor.")


def text2speech(text: str):
    """Utility function: Convert text to speech once."""
    config = Config()
    manager = TextToSpeechManager(config)
    manager.text_to_speech(text)


def main():
    config = Config()
    manager = TextToSpeechManager(config)
    manager.monitor_clipboard()


if __name__ == "__main__":
    main()
