import queue
import shlex
import signal
import subprocess
import threading
import time
import cv2


class DJICameraMedia:
    def __init__(self, drone_ip, frame="buffer.jpg", download="output.mp4", fps=10):
        self.running = False
        self.frame_counter = -1
        self.frame_queue = None
        self.fps = fps
        self.frame = "buffer.jpg"
        self.processing_thread = None
        self.reading_thread = None
        self.source = f"rtsp://aaa:aaa@{drone_ip}:8554/streaming/live/1"
        self.record_command = f'ffmpeg -i {self.source} -c copy {download}'
        self.recording_process = None
        self.stream_command = f'ffmpeg -i {self.source} -vf fps={fps} -update 1' + \
            f'-hls_flags temp_file {frame} -y '
        self.streaming_process = None

    def setup_recording(self):
        # TODO: check if DJI needs any set up
        pass

    def start_recording(self):
        self.recording_process = subprocess.Popen(
            shlex.split(self.record_command))

    def setup_stream(self, live_callback=None):
        self.frame_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=live_callback)
        self.reading_thread = threading.Thread(target=self.read)

    def start_stream(self):
        self.running = True
        self.streaming_process = subprocess.Popen(
            shlex.split(self.stream_command))
        self.reading_thread.start()
        self.processing_thread.start()

    def read(self):
        try:
            frame = cv2.imread(self.frame)
            self.frame_queue.put_nowait(frame)
        except Exception:
            time.sleep(1 / self.fps)

    def stop_stream(self):
        self.running = False
        self.processing_thread.join()
        self.reading_thread.join()
        self.streaming_process.send_signal(signal.SIGINT)
        self.streaming_process.wait()

    def stop_recording(self):
        self.recording_process.send_signal(signal.SIGINT)
        self.recording_process.wait()

    def download_last_media(self):
        # TODO: move output.mp4 to download location
        pass
