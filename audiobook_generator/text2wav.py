import io
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf
import torch
from kokoro import KPipeline
from speedy_utils import identify, memoize
import pydub
from pydub import AudioSegment

from audiobook_generator.wav_to_mp3 import wav_to_mp3


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
    DEVICE: str = "cpu"


class TextToSpeech:
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        self.config = config
        self.pipeline = None

    def preprocess(self, text: str):
        # text = text.lower()
        special_characters = {
            "’": "'",
            "‘": "'",
            "&": "",
            "@": "",
            "#": "",
            "$": "",
            "%": "",
            "^": "",
            "*": "",
            # "(": "",
            # ")": "",
            # "-": "",
            # "_": "",
            # "+": "",
            # "{": "",
            # "}": "",
            # "[": "",
            # "]": "",
            # "|": "",
            # "\\": "",
            # ":": "",
            # ";": "",
            # "\"": "",
            # "<": "",
            # ">": "",
            # "!": "",
            # "`": "",
            # "~": "",
            # "·": "",
        }
        for char, replacement in special_characters.items():
            text = text.replace(char, replacement)
        return text

    def generate(self, text: str, format: str = "wav"):
        text = self.preprocess(text)
        id = identify([text, self.config.VOICE, self.config.SPEED])
        output_path = Path(f"assets/{id}.wav")
        if output_path.exists():
            return f"{id}.{format}"

        def _generate_audio(text, voice, speed):
            generator = self.pipeline(
                text,
                voice=voice,
                speed=speed,
                split_pattern=r"\n+",
            )
            return generator

        if not self.pipeline:
            self.initialize_pipeline()

        generator = _generate_audio(text, self.config.VOICE, self.config.SPEED)
        output_path.parent.mkdir(exist_ok=True)

        all_audio = []
        for _, _, audio in generator:
            all_audio.append(audio)
        if not all_audio:
            return

        final_audio = torch.cat(all_audio, dim=0).numpy()

        # if format == "wav":
        sf.write(str(output_path), final_audio, self.config.SAMPLE_RATE)
        if format == "mp3":
            wav_to_mp3(str(output_path), str(output_path.with_suffix(".mp3")))

        else:
            raise ValueError(f"Unsupported format: {format}")

        return f"{id}.{format}"

    def initialize_pipeline(self):
        self.pipeline = KPipeline(lang_code=self.config.LANG_CODE)
