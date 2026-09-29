# AudioPulse

Desktop music player built with Python, Tkinter, Pygame and Matplotlib.

## Features

- MP3 playback
- Play, pause, stop and mute controls
- Playback progress and seeking
- Track title and artist metadata
- Real-time audio visualization
- Simple desktop interface

## Requirements

- Python 3.10+
- FFmpeg installed and available in `PATH`
- Python packages listed in `requirements.txt`


Install FFmpeg separately and make sure the `ffmpeg` command is available from the terminal.


Place MP3 files in the project root to have them detected by the current player implementation.

## Project structure

```text
AudioPulse/
├── images/
│   ├── images.png
│   ├── mute.png
│   ├── pause.png
│   ├── play.png
│   └── stop.png
├── Playlist/
│   └── .gitkeep
├── .gitignore
├── music_player.py
├── requirements.txt
└── README.md
```
