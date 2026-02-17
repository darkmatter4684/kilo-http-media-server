"""
Kilo HTTP Media Server
A lightweight HTTP media server for viewing photos and videos.
"""
import os
import random
import argparse
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configuration
app = FastAPI(title="Kilo HTTP Media Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Image and video extensions
IMG_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}
VID_EXTS = {"mp4", "mov", "avi", "mkv", "webm"}

# Global configuration (will be set via CLI args)
MEDIA_ROOT = None


def get_media_root() -> Path:
    """Get the configured media root path."""
    if MEDIA_ROOT is None:
        raise HTTPException(
            status_code=500,
            detail="Media root not configured. Set MEDIA_ROOT environment variable or use --media-root CLI argument."
        )
    return Path(MEDIA_ROOT)


def is_media_file(filename: str, media_type: Optional[str] = None) -> bool:
    """Check if a file is a media file."""
    ext = filename.lower().split('.')[-1]
    if media_type == "images":
        return ext in IMG_EXTS
    elif media_type == "videos":
        return ext in VID_EXTS
    else:
        return ext in IMG_EXTS or ext in VID_EXTS


def get_media_type(filename: str) -> Optional[str]:
    """Get the media type of a file."""
    ext = filename.lower().split('.')[-1]
    if ext in IMG_EXTS:
        return "images"
    elif ext in VID_EXTS:
        return "videos"
    return None


def relative_to_media_root(path: Path) -> str:
    """Get path relative to media root."""
    media_root = get_media_root()
    try:
        return str(path.relative_to(media_root))
    except ValueError:
        # Path is not relative to media root
        return str(path)


@app.get("/")
async def root(request: Request):
    """Serve the main page."""
    from fastapi.responses import HTMLResponse
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kilo Media Server</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a2e;
                color: #eee;
                min-height: 100vh;
                padding: 20px;
            }
            h1 { text-align: center; margin-bottom: 30px; color: #00d9ff; }
            .container { max-width: 800px; margin: 0 auto; }
            .path-display {
                background: #16213e;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                overflow-x: auto;
            }
            .path-display a {
                color: #00d9ff;
                text-decoration: none;
            }
            .path-display a:hover { text-decoration: underline; }
            .breadcrumb { color: #888; }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 15px;
            }
            .item {
                background: #16213e;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                cursor: pointer;
                transition: transform 0.2s, background 0.2s;
            }
            .item:hover {
                transform: scale(1.05);
                background: #1f3460;
            }
            .item-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .item-name {
                font-size: 14px;
                word-break: break-word;
            }
            .item-count {
                font-size: 12px;
                color: #888;
                margin-top: 5px;
            }
            .media-links {
                display: flex;
                gap: 10px;
                justify-content: center;
                margin-top: 20px;
            }
            .media-link {
                background: #00d9ff;
                color: #1a1a2e;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                transition: transform 0.2s;
            }
            .media-link:hover {
                transform: scale(1.05);
            }
            .empty { text-align: center; color: #888; padding: 40px; }
            .error { color: #ff6b6b; text-align: center; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📁 Kilo Media Server</h1>
            <div id="content">
                <p class="empty">Loading...</p>
            </div>
        </div>
        <script>
            let currentPath = '';
            
            async function loadDirectory(path = '') {
                const content = document.getElementById('content');
                content.innerHTML = '<p class="empty">Loading...</p>';
                
                try {
                    const response = await fetch('/api/directories' + (path ? '?path=' + encodeURIComponent(path) : ''));
                    const data = await response.json();
                    
                    let html = '';
                    
                    // Breadcrumb navigation
                    if (data.path) {
                        html += '<div class="path-display">';
                        html += '<span class="breadcrumb">';
                        html += '<a href="#" onclick="loadDirectory(\\'\\'); return false;">Root</a>';
                        
                        let breadcrumbPath = '';
                        const parts = data.path.split(/[/\\\\]/).filter(p => p);
                        for (const part of parts) {
                            breadcrumbPath += (breadcrumbPath ? '/' : '') + part;
                            html += ' / <a href="#" onclick="loadDirectory(\\'' + breadcrumbPath + '\\'); return false;">' + part + '</a>';
                        }
                        html += '</span>';
                        html += '</div>';
                    }
                    
                    html += '<div class="grid">';
                    
                    // Directories
                    for (const dir of data.directories || []) {
                        const dirPath = dir.path;
                        const imgCount = dir.image_count || 0;
                        const vidCount = dir.video_count || 0;
                        const total = imgCount + vidCount;
                        
                        html += '<div class="item" onclick="loadDirectory(\\'' + dirPath + '\\')">';
                        html += '<div class="item-icon">📁</div>';
                        html += '<div class="item-name">' + dir.name + '</div>';
                        if (total > 0) {
                            html += '<div class="item-count">' + (imgCount ? '🖼️' + imgCount : '') + (vidCount ? ' 🎬' + vidCount : '') + '</div>';
                        }
                        html += '</div>';
                    }
                    
                    html += '</div>';
                    
                    // Media links if there are media files
                    if (data.image_count > 0 || data.video_count > 0) {
                        html += '<div class="media-links">';
                        if (data.image_count > 0) {
                            html += '<a class="media-link" href="/slideshow/images?path=' + encodeURIComponent(path || '') + '">🖼️ Images (' + data.image_count + ')</a>';
                        }
                        if (data.video_count > 0) {
                            html += '<a class="media-link" href="/slideshow/videos?path=' + encodeURIComponent(path || '') + '">🎬 Videos (' + data.video_count + ')</a>';
                        }
                        html += '</div>';
                    }
                    
                    if ((data.directories || []).length === 0 && data.image_count === 0 && data.video_count === 0) {
                        html += '<p class="empty">No media files found in this directory.</p>';
                    }
                    
                    content.innerHTML = html;
                } catch (error) {
                    content.innerHTML = '<p class="error">Error loading directory: ' + error.message + '</p>';
                }
            }
            
            // Load root directory on page load
            loadDirectory('');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/directories")
async def list_directories(path: Optional[str] = Query(None)):
    """List directories and media files in a given path."""
    try:
        media_root = get_media_root()
        
        if path:
            target_dir = media_root / path
        else:
            target_dir = media_root
        
        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        directories = []
        image_count = 0
        video_count = 0
        
        for item in sorted(target_dir.iterdir()):
            if item.is_dir():
                # Count media in subdirectory
                img_count = 0
                vid_count = 0
                try:
                    for sub_item in item.iterdir():
                        if sub_item.is_file() and is_media_file(sub_item.name):
                            if get_media_type(sub_item.name) == "images":
                                img_count += 1
                            else:
                                vid_count += 1
                except PermissionError:
                    pass
                
                directories.append({
                    "name": item.name,
                    "path": relative_to_media_root(item),
                    "image_count": img_count,
                    "video_count": vid_count
                })
            elif item.is_file() and is_media_file(item.name):
                if get_media_type(item.name) == "images":
                    image_count += 1
                else:
                    video_count += 1
        
        return {
            "path": path or "",
            "directories": directories,
            "image_count": image_count,
            "video_count": video_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media")
async def list_media(path: Optional[str] = Query(None), media_type: Optional[str] = Query(None)):
    """List media files in a directory."""
    try:
        media_root = get_media_root()
        
        if path:
            target_dir = media_root / path
        else:
            target_dir = media_root
        
        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        images = []
        videos = []
        
        for item in sorted(target_dir.iterdir()):
            if item.is_file() and is_media_file(item.name, media_type):
                media_t = get_media_type(item.name)
                if media_t == "images":
                    images.append({
                        "name": item.name,
                        "path": relative_to_media_root(item)
                    })
                elif media_t == "videos":
                    videos.append({
                        "name": item.name,
                        "path": relative_to_media_root(item)
                    })
        
        return {
            "path": path or "",
            "images": images,
            "videos": videos
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_slideshow_html(media_type: str, path: str, randomize: bool) -> str:
    """Generate the slideshow HTML."""
    try:
        media_root = get_media_root()
        
        if path:
            target_dir = media_root / path
        else:
            target_dir = media_root
        
        if not target_dir.exists():
            return '<div class="empty">Directory not found</div>'
        
        media_files = []
        for item in sorted(target_dir.iterdir()):
            if item.is_file() and is_media_file(item.name, media_type):
                media_files.append({
                    "name": item.name,
                    "path": relative_to_media_root(item)
                })
        
        if randomize:
            random.shuffle(media_files)
        
        media_json = str(media_files).replace("'", '"')
        icon = "🖼️" if media_type == "images" else "🎬"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
            <title>{icon} {media_type.title()} Slideshow</title>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                html, body {{
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    background: #000;
                    touch-action: none;
                }}
                .media-container {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .media-container img, .media-container video {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                }}
                .controls {{
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    padding: 15px 25px;
                    background: rgba(30, 30, 30, 0.9);
                    border-radius: 50px;
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    opacity: 0;
                    transition: opacity 0.3s;
                    z-index: 100;
                }}
                .controls.visible {{ opacity: 1; }}
                .controls button {{
                    background: #444;
                    border: none;
                    color: white;
                    width: 50px;
                    height: 50px;
                    font-size: 20px;
                    border-radius: 50%;
                    cursor: pointer;
                    transition: background 0.2s, transform 0.1s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .controls button:hover {{ background: #666; }}
                .controls button:active {{ transform: scale(0.95); }}
                .progress {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    padding: 15px;
                    background: linear-gradient(rgba(0,0,0,0.8), transparent);
                    color: white;
                    font-size: 16px;
                    text-align: center;
                    opacity: 0;
                    transition: opacity 0.3s;
                }}
                .progress.visible {{ opacity: 1; }}
                .loading {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: white;
                    font-size: 24px;
                }}
                .empty {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #888;
                    font-size: 20px;
                    text-align: center;
                }}
                .back-link {{
                    position: fixed;
                    top: 15px;
                    left: 15px;
                    background: rgba(255,255,255,0.2);
                    color: white;
                    padding: 10px 15px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 14px;
                    z-index: 100;
                }}
                .back-link:hover {{ background: rgba(255,255,255,0.4); }}
            </style>
        </head>
        <body>
            <a href="/" class="back-link">← Back</a>
            
            <div class="progress" id="progress">1 / 1</div>
            
            <div class="media-container" id="mediaContainer">
                <div class="loading" id="loading">Loading...</div>
            </div>
            
            <div class="controls" id="controls">
                <button id="shuffle">🔀</button>
                <button id="prev">◀</button>
                <button id="playPause">⏸</button>
                <button id="next">▶</button>
            </div>
            
            <script>
                const mediaFiles = {media_json};
                const mediaType = '{media_type}';
                let currentIndex = 0;
                let isPlaying = true;
                let autoAdvance = null;
                let controlsVisible = true;
                let hideControlsTimeout = null;
                
                const container = document.getElementById('mediaContainer');
                const progress = document.getElementById('progress');
                const controls = document.getElementById('controls');
                const prev = document.getElementById('prev');
                const next = document.getElementById('next');
                const playPause = document.getElementById('playPause');
                const shuffle = document.getElementById('shuffle');
                
                function showMedia(index) {{
                    if (mediaFiles.length === 0) {{
                        container.innerHTML = '<div class="empty">No media found</div>';
                        return;
                    }}
                    
                    currentIndex = index;
                    if (currentIndex < 0) currentIndex = mediaFiles.length - 1;
                    if (currentIndex >= mediaFiles.length) currentIndex = 0;
                    
                    progress.textContent = (currentIndex + 1) + ' / ' + mediaFiles.length;
                    
                    container.innerHTML = '<div class="loading">Loading...</div>';
                    
                    const file = mediaFiles[currentIndex];
                    const mediaPath = '/media/' + encodeURIComponent(file.path);
                    
                    const media = document.createElement(mediaType === 'images' ? 'img' : 'video');
                    media.id = 'media';
                    media.src = mediaPath;
                    media.alt = file.name;
                    
                    if (mediaType === 'videos') {{
                        media.autoplay = true;
                        media.loop = true;
                    }}
                    
                    // Add media to container immediately
                    container.innerHTML = '';
                    container.appendChild(media);
                    
                    // Preload next
                    if (currentIndex + 1 < mediaFiles.length) {{
                        const nextFile = mediaFiles[currentIndex + 1];
                        const nextPath = '/media/' + encodeURIComponent(nextFile.path);
                        new Image().src = nextPath;
                    }}
                }}
                
                function togglePlay() {{
                    isPlaying = !isPlaying;
                    playPause.textContent = isPlaying ? '⏸' : '▶';
                    const media = document.getElementById('media');
                    if (media) {{
                        if (isPlaying) {{
                            media.play();
                        }} else {{
                            media.pause();
                        }}
                    }}
                }}
                
                function showControls() {{
                    controls.classList.add('visible');
                    progress.classList.add('visible');
                    controlsVisible = true;
                    clearTimeout(hideControlsTimeout);
                    if (isPlaying) {{
                        hideControlsTimeout = setTimeout(() => {{
                            controls.classList.remove('visible');
                            progress.classList.remove('visible');
                            controlsVisible = false;
                        }}, 3000);
                    }}
                }}
                
                prev.onclick = () => showMedia(currentIndex - 1);
                next.onclick = () => showMedia(currentIndex + 1);
                playPause.onclick = togglePlay;
                shuffle.onclick = function() {{
                    for (let i = mediaFiles.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [mediaFiles[i], mediaFiles[j]] = [mediaFiles[j], mediaFiles[i]];
                    }}
                    showMedia(0);
                }};
                
                document.onclick = showControls;
                document.ontouchstart = showControls;
                
                // Keyboard navigation
                document.onkeydown = (e) => {{
                    if (e.key === 'ArrowLeft') showMedia(currentIndex - 1);
                    if (e.key === 'ArrowRight') showMedia(currentIndex + 1);
                    if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
                }};
                
                // Swipe navigation
                let touchStartX = 0;
                document.ontouchstart = (e) => {{
                    touchStartX = e.touches[0].clientX;
                }};
                document.ontouchend = (e) => {{
                    const touchEndX = e.changedTouches[0].clientX;
                    const diff = touchStartX - touchEndX;
                    if (Math.abs(diff) > 50) {{
                        if (diff > 0) showMedia(currentIndex + 1);
                        else showMedia(currentIndex - 1);
                    }}
                }};
                
                // Initial load
                showMedia(0);
            </script>
        </body>
        </html>
        """
        return html_content
        
    except Exception as e:
        return f'<div class="empty">Error: {str(e)}</div>'


@app.get("/slideshow/{media_type}")
async def slideshow_page(media_type: str, path: Optional[str] = Query(None), randomize: bool = Query(False)):
    """Serve the slideshow page."""
    if media_type not in ["images", "videos"]:
        raise HTTPException(status_code=404, detail="Invalid media type")
    
    html_content = generate_slideshow_html(media_type, path or "", randomize)
    return HTMLResponse(content=html_content)


@app.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """Serve a media file."""
    try:
        media_root = get_media_root()
        file_path_obj = media_root / file_path
        
        # Security check: ensure the file is within media root
        file_path_obj = file_path_obj.resolve()
        media_root_resolved = media_root.resolve()
        
        if not str(file_path_obj).startswith(str(media_root_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path_obj.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path_obj.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        # Determine content type
        ext = file_path.lower().split('.')[-1]
        content_type = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'mkv': 'video/x-matroska',
            'webm': 'video/webm'
        }.get(ext, 'application/octet-stream')
        
        return FileResponse(
            file_path_obj,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Kilo HTTP Media Server")
    parser.add_argument(
        "--media-root",
        type=str,
        default=os.environ.get("MEDIA_ROOT"),
        help="Path to media directory (default: MEDIA_ROOT env var)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("HOST", "0.0.0.0"),
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 8000)),
        help="Server port (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if not args.media_root:
        parser.error("--media-root is required")
    
    global MEDIA_ROOT
    MEDIA_ROOT = args.media_root
    
    print(f"Starting Kilo HTTP Media Server...")
    print(f"Media root: {MEDIA_ROOT}")
    print(f"Server running at http://{args.host}:{args.port}")
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
