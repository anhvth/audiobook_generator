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

# Example usage:
if __name__ == '__main__':
    # Sample text simulating the provided input.
    sample_text = """
- **An Easy & Proven Way to**
- **Build Good Habits & Break Bad Ones**

**James Clear**

An Easy & Proven Way
to Build Good Habits &
Break Bad Ones

AVERY

an imprint of Penguin Random House

New York

![](_page_2_Picture_0.jpeg)

Copyright © 2018 by James Clear

<span id="page-2-0"></span>
Penguin supports copyright. Copyright fuels creativity, encourages diverse voices, promotes free speech, and creates a vibrant culture. Thank you for buying an authorized edition of this book and for complying with copyright laws by not reproducing, scanning, or distributing any part of it in any form without permission. You are supporting writers and allowing Penguin to continue to publish books for every reader.

## **Ebook ISBN 9780735211308**

While the author has made every effort to provide accurate Internet addresses at the time of publication, neither the publisher nor the author assumes any responsibility for errors, or for changes that occur after publication. Further, the publisher does not have any control over and does not assume any responsibility for author or third-party websites or their content.

Version_1

#### <span id="page-4-0"></span>**a·tom·ic**

#### əˈtämik

- 1. an extremely small amount of a thing; the single irreducible unit of a larger system.
- 2. the source of immense energy or power.

#### **hab·it**

#### ˈhabət

- 1. a routine or practice performed regularly; an automatic response to a specific situation.
    """
    
    pages = chunk_into_pages(sample_text)
    for idx, page in enumerate(pages, 1):
        print(f"--- Page {idx} ---")
        print(page)
        print()
