"""LiveKit WebRTC video stream handler."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Optional

import cv2
import numpy as np
from livekit import rtc
from loguru import logger


class LiveKitVideoStream:
    """LiveKit WebRTC video stream capture."""

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self._room: Optional[rtc.Room] = None
        self._video_track: Optional[rtc.VideoTrack] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        """Start the LiveKit connection and frame capture."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

        # Wait for connection
        timeout = 10
        start_time = time.time()
        while self._room is None and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if self._room is None:
            raise RuntimeError(f"Failed to connect to LiveKit room at {self.url}")

    def stop(self) -> None:
        """Stop the LiveKit connection."""
        self._running = False
        if self._loop and self._room:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)

    def _run_async_loop(self) -> None:
        """Run the asyncio event loop in a separate thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._connect_and_run())
        except Exception as e:
            logger.error(f"LiveKit connection error: {e}")
        finally:
            self._loop.close()

    async def _connect_and_run(self) -> None:
        """Connect to LiveKit room and handle events."""
        self._room = rtc.Room()

        # Set up event handlers
        @self._room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            logger.info(f"Track subscribed: {track.kind}")
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._video_track = track
                # Start video stream processing
                asyncio.create_task(self._process_video_stream(track))

        try:
            await self._room.connect(self.url, self.token)
            logger.info("Connected to LiveKit room")

            # Keep the connection alive
            while self._running:
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to connect to LiveKit: {e}")
            raise
        finally:
            await self._disconnect()

    async def _process_video_stream(self, track: rtc.RemoteVideoTrack) -> None:
        """Process video frames from the track."""
        logger.info("Starting video stream processing")
        try:
            # Create video stream from track
            stream = rtc.VideoStream.from_track(track=track)
            logger.info("Starting frame processing loop")
            
            async for event in stream:
                try:
                    # Extract frame from event
                    frame = event.frame
                    
                    # Convert LiveKit VideoFrame to numpy array
                    width, height = frame.width, frame.height
                    buffer_type = frame.type
                    
                    # Convert memoryview to numpy array
                    data = frame.data
                    if isinstance(data, memoryview):
                        data = np.frombuffer(data, dtype=np.uint8)
                    
                    # Ensure we have a contiguous numpy array
                    data = np.asarray(data, dtype=np.uint8)

                    # Reshape based on buffer type
                    if buffer_type == rtc.VideoBufferType.RGBA:
                        img_array = data.reshape((height, width, 4))
                        # Convert RGBA to BGR for OpenCV compatibility
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                    elif buffer_type == rtc.VideoBufferType.RGB24:
                        img_array = data.reshape((height, width, 3))
                        # Convert RGB to BGR for OpenCV compatibility
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    elif buffer_type in (rtc.VideoBufferType.ARGB, rtc.VideoBufferType.ABGR, rtc.VideoBufferType.BGRA):
                        # ARGB/ABGR/BGRA are 4-channel formats; convert to BGR
                        img_array = data.reshape((height, width, 4))
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                    elif buffer_type == rtc.VideoBufferType.I420:
                        # I420 is YUV420 planar (Y plane, U plane, V plane)
                        expected_len = height * width * 3 // 2
                        if data.size != expected_len:
                            logger.warning(
                                "I420 frame size mismatch (expected %d, got %d), skipping",
                                expected_len,
                                data.size,
                            )
                            continue
                        yuv = data.reshape((height * 3 // 2, width))
                        img_array = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
                    elif buffer_type == rtc.VideoBufferType.NV12:
                        # NV12 is a common YUV420 semi-planar format
                        expected_len = height * width * 3 // 2
                        if data.size != expected_len:
                            logger.warning(
                                "NV12 frame size mismatch (expected %d, got %d), skipping",
                                expected_len,
                                data.size,
                            )
                            continue
                        yuv = data.reshape((height * 3 // 2, width))
                        img_array = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)
                    else:
                        # Unsupported format; don't spam the log too much.
                        logger.warning("Unsupported buffer type: %s, skipping frame", buffer_type)
                        continue

                    # Store latest frame for consumers (e.g. VideoStream.get_latest_frame)
                    with self._lock:
                        self._latest_frame = img_array
                except Exception as e:
                    logger.error(f"Error processing LiveKit frame: {e}")

        except Exception as e:
            logger.error(f"Error in video stream processing: {e}")

    async def _disconnect(self) -> None:
        """Disconnect from the room."""
        if self._room:
            await self._room.disconnect()
            self._room = None
            self._video_track = None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest video frame."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None