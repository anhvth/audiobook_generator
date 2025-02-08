# Audiobook Generator

## Installation

To install the Audiobook Generator, run the following command:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
pip install https://github.com/anhvth/audiobook_generator.git
```

## Usage

To generate an audiobook from a PDF file, use the following command:

```bash
OUTPUT_DIR=output/full/
PDF=/tmp/atomic-hatbits.pdf
PDF_NAME=$(basename $PDF)
marker_single $PDF --use_llm --google_api_key $GOOGLE_API_KEY --output_dir $OUTPUT_DIR
mdfile=$OUTPUT_DIR/${PDF_NAME%.pdf}/${PDF_NAME%.pdf}.md
# check existance of the md file
if [ ! -f "$mdfile" ]; then
    echo "Error: $mdfile not found"
fi
export_audiobook "$mdfile" $OUTPUT_DIR --book_name="Atomic Habit" -i
cp -r output/full/atomic-hatbits/*.jpeg output/full/
```
