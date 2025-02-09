import os
import dspy
from openai import BaseModel
import dspy
from openai import BaseModel
from loguru import logger

model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
logger.info(f"Using model: {model}, to change set the LLM_MODEL environment variable.")
lm = dspy.LM(model, max_tokens=4000)
dspy.configure(lm=lm)


# --- For text processing and TTS
class MarkdownFormat(dspy.Signature):
    """
    Convert raw paragraph to markdown formatted text.
    Utilize `#` for headings, `*` for bullet points, and `-` for numbered lists. Properly add newline to improve readability.
    """

    raw_text: str = dspy.InputField()
    markdown: str = dspy.OutputField()


md_formated_llm = dspy.Predict(MarkdownFormat)


# --- For text processing and TTS
class ParaGraph(BaseModel):
    title: str
    text: str


class RawTextToParagraphs(dspy.Signature):
    """
    Process raw text to paragraphs.

    Splits the text into paragraphs based on newlines and removes special characters like `#`, `*`, `-`, etc.
    In addition, ensure that each paragraph is not too short: if a split results in a paragraph with fewer than
    50 words, merge it with an adjacent paragraph so that each paragraph expresses a complete idea.

    The output is a list of ParaGraph objects where each paragraph meets the minimum length requirement.
    """

    raw_text: str = dspy.InputField()
    paragraphs: list[ParaGraph] = dspy.OutputField()


raw_text_to_paragraphs = dspy.Predict(RawTextToParagraphs)
# --- Improve transcript


class ImproveTranscript(dspy.Signature):
    """
    Two main tasks: clean transcript for TTS and format markdown for readability.

    1. Transcript Improvement:
    - Remove all formatting markers (*, #, -, etc.)
    - Remove redundant text like copyright notices
    - Clean up extra spaces and newlines
    - Keep only the essential content for clear audio narration
    - Remove any text in parentheses with citations or references
    - Replace abbreviations with full words (e.g., "Dr." to "Doctor")

    2. Markdown Formatting:
    - Format titles with # (main) or ## (subtitles)
    - Emphasize author names with *italic*
    - Format quotes with > blockquotes
    - Create proper bullet lists with *
    - Use numbered lists with 1. 2. 3.
    - Format URLs as [text](url)
    - Format emails as [email](mailto:email)
    - Use **bold** for important concepts
    - Add horizontal rules (---) between major sections

    Examples:
    Input: An easy and proven way to build good habits and break bad ones by James Clear. Copyright © 2018 by James Clear.
    Output:
    Improve transcript: An easy and proven way to build good habits and break bad ones by James Clear.
    Improve markdown: # An easy and proven way to build good habits and break bad ones
    By *James Clear*
    """

    text: str = dspy.InputField()
    improve_transcript: str = dspy.OutputField()
    improve_markdown: str = dspy.OutputField()


text_improver = dspy.Predict(ImproveTranscript)


# --- Split text

from typing import List, Optional
from pydantic import Field


class ChunkFormat(BaseModel):

    title: str = Field(description="The title of the chunk.")
    text: str = Field(
        description="The formated text. Should be 300-500 words for optimal TTS processing."
    )


class SplitText(dspy.Signature):
    """
    Split multiple pages into chunks optimized for audio narration.
    Rules:
        - Each chunk should be 300-500 words for optimal TTS processing
        - Keep titles with their related paragraphs in the same chunk
        - Preserve natural paragraph breaks and semantic units
        - Never split sentences in the middle
        - Keep hierarchical structure (title -> subtitles -> content)
        - If a section is longer than 500 words, split at the most logical break point
        - If a section is shorter than 300 words, combine with adjacent related content
        - Maintain the original meaning and context of the content
        - Do not alter, remove or add any content - only restructure.
        - Remove metadata like page numbers, headers, footers, and other non-essential text
        - The output chunks together must cover the entire input text
    Here is how example output should look like:
    ```
    [
        {
            "title": "Chapter 1: The Beginning",
            "text": "This is the first paragraph of the chapter. This is the second paragraph of the chapter."
        },
        {
            "title": "Chapter 2: The Middle",
            "text": "This is the first paragraph of the chapter. This is the second paragraph of the chapter."
        }
    ]
    """

    long_text: str = dspy.InputField()
    output_chunks: List[ChunkFormat] = dspy.OutputField()


split_text = dspy.Predict(SplitText)

__all__ = ["raw_text_to_paragraphs", "md_formated_llm", "text_improver", "split_text"]
