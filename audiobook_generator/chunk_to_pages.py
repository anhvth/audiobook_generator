import re
import numpy as np
from loguru import logger
from speedy_utils import flatten_list, multi_thread


def chunk_into_pages(text):
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
    pages = repartition(pages)
    return pages


from .chatgpt_format_text import split_text


def repartition(pages, word_per_page=300):
    def word_count(text):
        return len(text.split())

    logger.info("Repartitioning pages...")
    mid_word_len = word_per_page
    logger.info(f"Calculated median length: {mid_word_len}")

    # for page in pages:
    def get_chunks(page):
        num_page = word_count(page) / mid_word_len
        if num_page > 1.5:
            target_num_chunks = int(num_page) + 1
            output_chunks = split_text(
                long_text=page, target_num_chunks=target_num_chunks
            ).output_chunks
        else:
            output_chunks = [page]
        return output_chunks
        # new_pages.extend(output_chunks)

    logger.info("Splitting pages...")
    list_chunks = multi_thread(
        get_chunks, pages, 128, desc="Splitting pages", verbose=True
    )
    ret = flatten_list(list_chunks)
    logger.info("Finished repartitioning pages. Total pages: {}".format(len(ret)))
    return ret
