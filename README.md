# Vision Robot Agent

Production-oriented Vision AI Agent for answering questions about a robot camera stream using:

- latest frame
- recent temporal scene memory
- OpenAI vision reasoning

Designed for local file-based development, and then for camera/RTSP/ROS integrations.

## Architecture

```mermaid
flowchart TD
    VS[Video Source\nlocal file / webcam / RTSP / LiveKit] --> FC[Frame Capture Service\nVideoStream]
    FC --> FS[Frame Sampling\nFrameSampler]
    FS --> SA[Scene Analyzer\nOpenAI Vision]
    SA --> SM[Scene Memory Store\nTemporalStore]
    UQ[User Question] --> AG[Vision AI Agent\nPrompt + Reasoning]
    SM --> AG
    FC --> AG
    AG --> API[FastAPI Backend]
    API --> WEB[Web Dashboard]
    API --> CLI[CLI Demo]
```

## Project Structure

```text
vision-robot-agent/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   └── routes.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── reasoning.py
│   │   └── vision_agent.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── scene_memory.py
│   │   └── temporal_store.py
│   ├── video/
│   │   ├── __init__.py
│   │   ├── camera_adapter.py
│   │   ├── frame_sampler.py
│   │   └── video_stream.py
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── scene_analyzer.py
│   │   └── image_utils.py
│   ├── openai_client/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── __init__.py
│   └── main.py
├── web/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── scripts/
│   ├── run_demo.py
│   └── load_video.py
├── tests/
│   ├── sample_videos/
│   ├── test_agent.py
│   ├── test_memory.py
│   └── test_video.py
├── docker/
│   └── Dockerfile
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## Features

- Modular architecture for AI/robotics pipelines
- Supports local file, webcam, RTSP, and LiveKit WebRTC source modes
- LiveKit frame capture now properly stores the latest frame for `/frame` and memory updates
- Frame sampling every 5s for scene memory updates
- Temporal memory window (time + max-entry capped)
- On-demand question answering (`/ask`) using latest frame + memory
- FastAPI backend with `/frame`, `/memory`, `/ask`, `/health`
- Lightweight web dashboard
- CLI demo loop (`python scripts/run_demo.py`)
- Unit tests with `pytest`
- Dockerized runtime

## Installation

1. Create Python environment (Python 3.10+)
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Copy and edit environment file

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` to use OpenAI Vision. Without a key, the app runs in fallback mode.

## Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_VISION_MODEL` (default `gpt-4.1-mini`)
- `OPENAI_REASONING_MODEL` (default `gpt-4.1-mini`)
- `VIDEO_SOURCE` (default `tests/sample_videos/test_video.mp4`)
- `VIDEO_SOURCE_TYPE` (`auto|file|webcam|rtsp|livekit`)
- `LIVEKIT_URL` (for livekit source)
- `LIVEKIT_TOKEN` (for livekit source)
- `MEMORY_RETENTION_SECONDS` (default `60`)
- `MEMORY_MAX_ENTRIES` (default `12`)
- `HOST`, `PORT`, `LOG_LEVEL`

## Running the System

### API Backend

```bash
python -m app.api.server
```

Backend default URL: `http://localhost:8000`

- API docs: `http://localhost:8000/docs`
- Web dashboard: `http://localhost:8000/dashboard`

### CLI Demo

```bash
python scripts/run_demo.py
```

Example questions:

- "Is there a person in the video?"
- "What objects are visible?"
- "What changed recently?"

### Video Source Configuration

The system supports multiple video source types:

- **Local file**: `tests/sample_videos/test_video.mp4`
- **Webcam**: Camera index (e.g., `0`)
- **RTSP stream**: `rtsp://user:pass@host:554/stream`
- **LiveKit WebRTC**: `ws://localhost:17880` (requires token and an active publisher in the room)

#### Switching Sources

Use the provided script to easily switch between sources:

```bash
# Switch to local test video
python scripts/switch_video_source.py file tests/sample_videos/test_video.mp4

# Switch to webcam
python scripts/switch_video_source.py webcam 0

# Switch to RTSP
python scripts/switch_video_source.py rtsp rtsp://user:pass@host:554/stream

# Switch to LiveKit
python scripts/switch_video_source.py livekit ws://localhost:17880 --livekit-token YOUR_TOKEN
```

Or manually edit the `.env` file and update `VIDEO_SOURCE` and `VIDEO_SOURCE_TYPE`.

#### Troubleshooting LiveKit / No Frame

- If `/frame` returns `503 Service Unavailable`, the app cannot get a valid frame yet.
- For LiveKit sources this usually means there is no active publisher in the room (or the token is invalid/expired).
- Check the server logs for messages like `No frame available yet` or `Failed to connect to LiveKit room`.

## API Usage

### `GET /frame`

Returns latest camera frame as JPEG.

### `GET /memory`

Returns recent scene observations.

Example response:

```json
{
  "observations": [
    {
      "timestamp": "2026-03-07T12:00:10.101010",
      "description": "A person is standing near a desk with a laptop."
    }
  ]
}
```

### `POST /ask`

Request:

```json
{
  "question": "Is someone in the room?"
}
```

Response:

```json
{
  "answer": "Yes, one person is visible near a desk."
}
```

## Docker

Build and run:

```bash
docker build -f docker/Dockerfile -t vision-robot-agent .
docker run --rm -p 8000:8000 --env-file .env vision-robot-agent
```

## Testing

```bash
pytest -q
```

## Engineering Notes

- Memory updates happen every `FRAME_SAMPLE_SECONDS` (default 5s)
- Memory is bounded by both time window and max entries
- Full frame-to-openai calls are **on-demand for questions** and sampled for memory summarization, not on every frame
- Default local dev source uses `tests/sample_videos/test_video.mp4`; if missing, a synthetic sample video is auto-generated.

## Future Extensions

- ROS topic adapter (`sensor_msgs/Image`)
- Better event detection / motion tracking pre-filter
- Optional vector memory backend (ChromaDB)
- Multi-camera support + agent routing
- Authentication, request quotas, observability dashboards
