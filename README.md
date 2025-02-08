# Audiobook Generator

## Installation

To install the Audiobook Generator, run the following command:

```bash
pip install https://github.com/anhvth/audiobook_generator.git
```

## Usage

To generate an audiobook from a PDF file, use the following command:

```bash
marker_single /tmp/atomic-hatbits.pdf --use_llm --google_api_key $GOOGLE_API_KEY --output_dir output/full/
```

To export the generated audiobook, use the following command:

```bash
mdfile_pattern=output/full/*.md
mdfile=$(ls $mdfile_pattern)
export_audiobook $mdfile --book_name="Atomic Habit" -i
```