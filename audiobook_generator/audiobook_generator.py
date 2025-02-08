import argparse
import sys
import os
import re
import shutil
from pathlib import Path

# --- Import FastHTML and Starlette classes
from fasthtml.common import *
from speedy_utils import multi_thread
from starlette.responses import FileResponse, RedirectResponse
from starlette.exceptions import HTTPException
from loguru import logger
from tqdm import tqdm

# --- For text processing and TTS
from audiobook_generator.chatgpt_format_text import (
    raw_text_to_paragraphs,
    md_formated_llm,
    text_improver,
)
from audiobook_generator.chunk_to_pages import chunk_into_pages
from audiobook_generator.text2wav import TextToSpeech

# --- For image generation
import requests


class AudioBookGenerator:
    def __init__(self, items, assets_dir="assets", with_image=False, to_md=True):
        """
        :param items: List of dictionaries containing text content
        :param assets_dir: Path to store generated audio/image assets
        :param with_image: Whether to generate images for each page
        """
        self.items = items
        self.assets_dir = Path(assets_dir)
        self.text2speech = TextToSpeech()
        self.with_image = with_image

        # Create assets directory if it doesn't exist
        self.assets_dir.mkdir(exist_ok=True)

        # Format the text as markdown for each item
        if to_md:
            for item in self.items:
                item["text_md"] = md_formated_llm(raw_text=item["text"]).markdown
        else:
            for item in self.items:
                item["text_md"] = item["text"]

    @classmethod
    def from_large_md(cls, md_file, page_rage):
        file = open(md_file, "r")
        pages: List[str] = chunk_into_pages(file.read())
        items = [{"text": p} for p in pages]
        if page_rage:
            # import ipdb; ipdb.set_trace()
            items = items[page_rage[0] : page_rage[1]]

        logger.info(f"Loaded {len(items)} pages from {md_file}")
        return cls(items, assets_dir="assets", with_image=False, to_md=False)

    def improve_transcript(self):
        # input is the text, output is the transcript with improved text
        logger.info("Improving transcript...")

        # for item in self.items:
        def process_one_item(item):
            try:
                item["improved_text"] = text_improver(
                    text=item["text_md"]
                ).improve_transcript
                item["text_md"] = text_improver(text=item["text_md"]).improve_markdown
                logger.info(f"Improved:``` {item['improved_text'][:60]}...```")
            except Exception as e:
                logger.error(f"Failed to improve item: {e}")
                item["improved_text"] = item["text_md"]
                item["text_md"] = item["text_md"]
            return item

        def process_one_item_3times(item):
            for i in range(3):
                try:
                    return process_one_item(item)
                except Exception as e:
                    logger.error(f"Failed to process item: {e}, try {i+1}/3")
            return item

        self.items = multi_thread(
            process_one_item_3times,
            self.items,
            verbose=True,
            desc="Improving transcript",
            workers=128,
        )

    @classmethod
    def from_txt(
        cls, input_file="./data/input.txt", assets_dir="assets", with_image=False
    ):
        """Create AudioBookGenerator from text file input.

        :param input_file: Path to the text file containing audiobook content
        :param assets_dir: Path to store generated audio/image assets
        :param with_image: Whether to generate images for each page
        """
        raw_text = open(input_file, encoding="utf-8").read()
        logger.info("Converting raw text to paragraphs...")
        paragraphs = raw_text_to_paragraphs(raw_text=raw_text).paragraphs
        items = [{"text": p.text} for i, p in enumerate(paragraphs) if len(p.text) > 50]
        return cls(items, assets_dir, with_image)

    def generate_audio(self):
        """Generate TTS audio files for each paragraph."""
        pbar = tqdm(self.items, desc="Generating audio", total=len(self.items))
        for item in pbar:
            preproc_text = item.get("improved_text", item["text"])
            logger.info(f"Generating audio from text: {preproc_text[:60]}...")
            item["audio"] = self.text2speech.generate(preproc_text)
        logger.info("All audio files are ready.")

    def generate_images(self):
        """
        Generate an image for each paragraph using the OpenAI image generation API.
        If you want to skip generation for an item that already has "image_url",
        you could adapt the logic here to respect user-supplied images.
        """
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_api_key:
            raise ValueError(
                "No OPENAI_API_KEY found in the environment. Cannot generate images."
            )

        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}",
        }

        for idx, item in enumerate(self.items):
            prompt_text = item["text"][:1000]  # or some truncated version
            logger.info(
                f"Generating image {idx+1}/{len(self.items)} with prompt: {prompt_text[:60]}..."
            )
            data = {
                "model": "dall-e-3",
                "prompt": prompt_text,
                "n": 1,
                "size": "1024x1024",
            }
            resp = requests.post(url, headers=headers, json=data)
            resp_json = resp.json()

            try:
                image_url = resp_json["data"][0]["url"]
            except (KeyError, IndexError):
                logger.error(f"Image generation failed for item {idx}: {resp_json}")
                continue

            image_data = requests.get(image_url).content
            image_filename = f"image_{idx}.png"
            image_path = self.assets_dir / image_filename
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)

            item["image"] = image_filename
        logger.info("All images have been generated.")
