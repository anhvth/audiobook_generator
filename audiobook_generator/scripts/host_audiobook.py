#!/usr/bin/env python
import argparse
from audiobook_generator.audiobook_app import AudioBookApp
from audiobook_generator.audiobook_generator import AudioBookGenerator
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Host AudioBook as a dynamic website")
    parser.add_argument("input_file", type=str, help="Path to the input text file")
    parser.add_argument(
        "--with_image",
        action="store_true",
        help="Generate an AI image for each page using OpenAI",
    )
    parser.add_argument(
        "--book_name",
        type=str,
        default="AudioBook",
        help="Name of the book to display in the browser tab",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port number to host the app"
    )
    parser.add_argument(
        "--improve_transcript",
        "-i",
        action="store_true",
        help="Use LLM to improve transcript by removing redundant markers",
    )
    args = parser.parse_args()

    # Instantiate and prepare the audiobook based on input file type
    if args.input_file.endswith(".md"):
        audio_book = AudioBookGenerator.from_large_md(args.input_file, page_rage=None)
    else:
        audio_book = AudioBookGenerator.from_txt(args.input_file)
    if args.improve_transcript:
        audio_book.improve_transcript()
    audio_book.generate_audio()
    if args.with_image:
        audio_book.generate_images()

    # Create the AudioBookApp instance
    audio_book_app = AudioBookApp(audio_book, args.book_name)

    # Run the app using Uvicorn on the specified host and port
    uvicorn.run(audio_book_app.app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
