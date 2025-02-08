import re
import numpy as np
from loguru import logger
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


def repartition(pages):
    logger.info("Repartitioning pages...")
    new_pages = []
    lens = [len(page) for page in pages]
    med_len = np.mean(lens)
    logger.info(f"Calculated median length: {med_len}")

    for page in pages:
        while len(page) > med_len * 1.5:
            half = len(page) // 2
            boundaries = []
            for pattern in [r'\n##\s\*\*', r'\n#\s', r'\.\n']:
                for match in re.finditer(pattern, page):
                    boundaries.append(match.start())
            if boundaries:
                split_idx = min(boundaries, key=lambda x: abs(x - half))
            else:
                split_idx = half
            logger.info(f"Splitting a page of length {len(page)} at index {split_idx}")
            new_pages.append(page[:split_idx].strip())
            page = page[split_idx:].strip()

        new_pages.append(page)
    logger.info("Finished repartitioning pages.")
    return new_pages
