import re
import numpy as np
from loguru import logger
from speedy_utils import flatten_list, multi_thread


def chunk_into_pages(text, page_range:tuple[int, int] = None):
    """
    Splits the input text into pages using HTML span page markers.

    A page marker is assumed to follow the pattern:
        <span id="page-<number>-<number>"></span>

    Args:
        text (str): The complete text content to be chunked.

    Returns:
        List[str]: A list of page contents as strings.
    """
    # Define the regex pattern to match the page markers.
    # This pattern looks for tags like <span id="page-2-0"></span>
    pattern = r'<span id="page-\d+-\d+"></span>'

    # Use re.split to break the text at each page marker.
    pages = re.split(pattern, text)

    # Remove any empty or whitespace-only pages
    pages = [page.strip() for page in pages if page.strip()]
    if page_range:
        start, end = page_range
        pages = pages[start:end]
    return repartition(pages)


from .chatgpt_format_text import split_text


def word_count(text):
    return len(text.split())


def split_long_page(page, target_wc):
    wc = word_count(page)
    pages = []
    while wc > target_wc:
        split_point = target_wc
        proposed_page = page[:split_point]
        # find the last newline before the split point
        new_split_point = proposed_page.rfind(".")
        proposed_page = page[:new_split_point]
        pages.append(proposed_page)
        page = page[new_split_point:]
        wc = word_count(page)
    pages.append(page)
    return pages


def repartition(pages, target_input_each=3000):

    inputs = []
    current_input = ""
    for page in pages:
        if word_count(current_input) + word_count(page) < target_input_each:
            current_input += page
        else:
            if len(current_input) > 0:
                inputs.append(current_input)
            current_input = page
    if len(current_input) > 0:
        inputs.append(current_input)

    new_inputs = []
    for i in inputs:
        if word_count(i) > target_input_each * 1.5:
            new_inputs.extend(split_long_page(i, target_input_each))
        else:
            new_inputs.append(i)
    inputs = new_inputs

    for i in inputs:
        print(word_count(i))

    run_outputs = multi_thread(
        lambda s: split_text(long_text=s, max_tokens=4000),
        inputs,
        desc="Splitting pages into chunks",
        workers=100,
        verbose=True,
    )
    outputs = []
    for run_output in run_outputs:
        outputs.extend(run_output.output_chunks)
    for i, out in enumerate(outputs):
        out = out.model_dump()
        out["text_md"] = out["text"]
        out['page_title'] = out['title']
        outputs[i] = out

    return outputs
