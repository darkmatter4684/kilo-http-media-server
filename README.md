# Kilo HTTP Media Server

A lightweight Python-based HTTP media server for viewing photos and videos from a local directory. Designed for mobile-friendly access on your local network.

## Features

- **Directory Browser** - Navigate through your media folders
- **Image Slideshow** - Full-screen image viewer with navigation
- **Video Slideshow** - Full-screen video player with auto-advance
- **Randomization** - Shuffle media with the shuffle button
- **Mobile-Friendly** - Touch controls, swipe navigation, responsive UI
- **Network Access** - Accessible from any device on your local network

## Supported Formats

| Images | Videos |
|--------|--------|
| JPG | MP4 |
| JPEG | MOV |
| PNG | AVI |
| GIF | MKV |
| WebP | WebM |

## Installation

```bash
# Install dependencies
uv sync
```

## Usage

```bash
# Basic usage (default port 8000)
uv run main.py --media-root /path/to/media

# Custom port
uv run main.py --media-root /path/to/media --port 9000

# Using environment variables
MEDIA_ROOT=/path/to/media PORT=9000 uv run main.py
```

## Access

- From same machine: `http://localhost:8000`
- From other devices: `http://[your-ip]:8000`

## URL Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Directory browser |
| `/slideshow/images?path=folder` | Image slideshow |
| `/slideshow/videos?path=folder` | Video slideshow |
| `/slideshow/images?path=folder&randomize=true` | Randomized slideshow |

## Controls

### Keyboard
- `←` / `→` - Previous / Next
- `Space` - Play / Pause

### Touch (Mobile)
- Swipe left/right to navigate
- Tap to show/hide controls

### On-Screen Buttons
- 🔀 Shuffle - Randomize order
- ◀ Previous - Go to previous media
- ⏸ Play/Pause - Toggle playback
- ▶ Next - Go to next media

## Configuration Options

| Option | CLI Argument | Environment Variable | Default |
|--------|--------------|---------------------|---------|
| Media Root | `--media-root` | `MEDIA_ROOT` | Required |
| Host | `--host` | `HOST` | `0.0.0.0` |
| Port | `--port` | `PORT` | `8000` |

## Example

```bash
# Windows
uv run main.py --media-root Z:\Photos --port 8080

# Linux/macOS
uv run main.py --media-root /mnt/media --port 8080
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Server**: Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS

## License

MIT License
