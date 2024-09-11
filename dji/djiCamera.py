import queue
import shlex
import signal
import subprocess
import threading


class DJICamera:
    def __init__(self, IP_RC, download='output.mp4'):
        self.running = False
        self.frame_counter = -1
        self.frame_queue = None
        self.processing_thread = None
        self.download = download
        self.source = f"rtsp://aaa:aaa@{IP_RC}:8554/streaming/live/1"
        self.record_command = f'ffmpeg -i {self.source} -c copy {self.download}'
        self.recording_process = None
        self.streaming_process = None

    def setup_recording(self):
        raise NotImplementedError()

    def start_recording(self):
        self.recording_process = subprocess.Popen(shlex.split(self.record_command))

    def setup_stream(self, live_callback=None):
        self.frame_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=live_callback)

    def start_stream(self):
        self.running = True
        self.processing_thread.start()

    def stop_stream(self):
        self.running = False
        self.processing_thread.join()

    def stop_recording(self):
        self.recording_process.send_signal(signal.SIGINT)
        self.recording_process.wait()

    def download_last_media(self):
        raise NotImplementedError()
