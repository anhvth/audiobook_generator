import io
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf
import torch
from kokoro import KPipeline
from speedy_utils import identify, memoize


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

    def generate(self, text: str):

        id = identify([text, self.config.VOICE, self.config.SPEED])
        output_path = Path(f"assets/{id}.wav")
        if output_path.exists():
            return f"{id}.wav"

        def _generate_audio(text, voice, speed):
            generator = self.pipeline(
                text,
                voice=voice,
                speed=speed,
                split_pattern=r"\n+",
            )
            return generator

        if not self.pipeline:
            self.pipeline = KPipeline(lang_code=self.config.LANG_CODE)

        generator = _generate_audio(text, self.config.VOICE, self.config.SPEED)
        output_path.parent.mkdir(exist_ok=True)

        # Collect all audio chunks
        all_audio = []
        for _, _, audio in generator:
            import ipdb; ipdb.set_trace()
            all_audio.append(audio)
        assert all_audio, "No audio chunks generated"
        # Concatenate all audio chunks
        final_audio = torch.cat(all_audio, dim=0).numpy()

        # Write the complete audio to file
        sf.write(str(output_path), final_audio, self.config.SAMPLE_RATE)
        return f"{id}.wav"
