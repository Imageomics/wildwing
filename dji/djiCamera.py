import queue
import threading


class DJICamera:
    def __init__(self):
        self.running = False
        self.frame_counter = 0
        self.frame_queue = queue.Queue()
        self.processing_thread = None

    def setup_recording(self):
        pass

    def start_recording(self):
        pass

    def setup_stream(self):
        pass

    def start_stream(self):
        pass

    def stop_stream(self):
        pass

    def stop_recording(self):
        pass

    def download_last_media(self):
        pass
