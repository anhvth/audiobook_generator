import dspy
from openai import BaseModel
import dspy
from openai import BaseModel


lm = dspy.LM("gpt-4o-mini", max_tokens=4000)
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
class SplitText(dspy.Signature):
    """
    Split a long piece of text into a specified number of roughly equal-sized chunks.
    
    The splitting process:
    - Preserves complete sentences and paragraphs where possible
    - Maintains all original formatting (markdown, lists, etc.)
    - Avoids splitting in the middle of words or formatting markers
    - Ensures each chunk is coherent and readable
    """

    long_text: str = dspy.InputField()
    target_num_chunks: int = dspy.InputField()
    output_chunks: list[str] = dspy.OutputField()


split_text = dspy.Predict(SplitText)

__all__ = ["raw_text_to_paragraphs", "md_formated_llm", "text_improver", "split_text"]
