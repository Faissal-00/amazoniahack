# Mosaic Web App

This is a minimal Streamlit demo for the AmazôniaHack Challenge 2 extraction pipeline.

It provides a graphical interface to upload document images, process them using the existing `scripts/` pipeline, and immediately view the structured extracted fields, confidence scores, and raw JSON output.

## Prerequisites

Ensure you have installed the project requirements:
```bash
pip install -r requirements.txt
```

## Running the App

Run this command from the repository root:
```bash
streamlit run website/app.py
```

This will launch the app and open it in your default web browser (typically at `http://localhost:8501`).

## How it works

1. **Upload**: Select a `.jpg`, `.jpeg`, or `.png` document from the Challenge 2 dataset.
2. **Extract**: The app saves the image to a temporary file and processes it using the exact same `OCREngine` and `extract_fields` functions as the CLI.
3. **View**: It visualizes the final output in an easy-to-read format without saving the files permanently to disk.
