import dspy
from openai import BaseModel
import dspy
from openai import BaseModel


lm = dspy.LM("gpt-4o-mini")
dspy.configure(lm=lm)

#--- For text processing and TTS
class MarkdownFormat(dspy.Signature):
    """
    Convert raw paragraph to markdown formatted text.
    Utilize `#` for headings, `*` for bullet points, and `-` for numbered lists. Properly add newline to improve readability.
    """

    raw_text: str = dspy.InputField()
    markdown: str = dspy.OutputField()


md_formated_llm = dspy.Predict(MarkdownFormat)

#--- For text processing and TTS
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


__all__ = ["raw_text_to_paragraphs", "md_formated_llm"]