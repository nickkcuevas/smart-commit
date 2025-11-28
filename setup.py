#!/usr/bin/env python3
"""
Setup script for smart-commit tool
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="smart-commit",
    version="1.0.0",
    description="Auto-generate descriptive commit messages using OpenAI or Groq",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/smart-commit",
    py_modules=["smart_commit"],
    entry_points={
        "console_scripts": [
            "smart-commit=smart_commit:cli",
        ],
    },
    install_requires=[
        "openai>=1.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "GitPython>=3.1.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)

