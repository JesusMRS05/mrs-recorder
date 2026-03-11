# MRS Recorder

A simple screen recorder that has a resizable capture frame, a start/stop button, and an output folder.

## Features

- Floating transparent capture frame
- Drag to move the frame
- Resize frame using corner and edge handles
- Start/stop recording button
- Output folder selector
- Automatic timestamped filenames
- Dark UI

## Dependencies

Install required packages:

```bash
pip install opencv-python mss numpy pillow
```
## Run

python src/main.py

## Output

Videos are saved as:

recording_YYYY-MM-DD_HH-MM-SS.avi

inside the selected output folder.