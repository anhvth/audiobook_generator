import re

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
    
    return pages
