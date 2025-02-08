import os
from setuptools import setup, find_packages

setup(
    name="read_my_clipboard",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyperclip",  # For clipboard operations
        "marker-pdf"
    ],
    author="anhvth",
    author_email="anhvth.226@gmail.com",
    description="A tool to read clipboard content",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/anhvth/read_my_clipboard",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'export_audiobook=audiobook_generator.scripts.export_audiobook:main',
        ],
    },
)