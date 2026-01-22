import speech_recognition as sr
import sounddevice as sd
import numpy as np
import threading
import queue
from PySide6.QtCore import QObject, Signal

class VoiceInputWorker(QObject):
    """Worker that handles speech recognition using sounddevice."""
    text_recognized = Signal(str)
    listening_started = Signal()
    listening_ended = Signal()
    error_occurred = Signal(str)
    audio_level_changed = Signal(float)

    def __init__(self, sample_rate=16000, block_size=1024):
        super().__init__()
        self.sample_rate = sample_rate
        self.block_size = block_size
        
        self._recognizer = sr.Recognizer()
        self._is_running = False
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue()
        self._thread = None

    def start(self):
        """Start the background listening process."""
        if self._is_running:
            return
            
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.listening_started.emit()

    def stop(self):
        """Stop listening."""
        self._is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.listening_ended.emit()

    def _run_loop(self):
        """Main capture loop."""
        # VAD Parameters
        silence_threshold = 0.01  # Lowered sensitivity
        silence_duration = 3.0    # Slightly shorter duration
        speech_buffer = []
        is_speaking = False
        silence_start_time = None
        
        print("DEBUG: Starting audio loop...")
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                              channels=1, 
                              callback=self._audio_callback,
                              blocksize=self.block_size,
                              dtype='int16'):
                
                print("DEBUG: Stream opened")
                
                while not self._stop_event.is_set():
                    try:
                        # Get audio data from queue
                        data = self._audio_queue.get(timeout=0.5)
                        
                        # Calculate audio level (RMS)
                        # Normalize 16-bit int to 0.0-1.0
                        floats = data.astype(np.float32) / 32768.0
                        rms = np.sqrt(np.mean(floats**2))
                        self.audio_level_changed.emit(float(rms * 10.0)) # Boost more for visual
                        
                        if rms > silence_threshold:
                            if not is_speaking:
                                print(f"DEBUG: Speech detected! (RMS: {rms:.4f})")
                            is_speaking = True
                            silence_start_time = None
                            speech_buffer.append(data)
                        else:
                            if is_speaking:
                                speech_buffer.append(data)
                                if silence_start_time is None:
                                    import time
                                    silence_start_time = time.time()
                                else:
                                    import time
                                    if time.time() - silence_start_time > silence_duration:
                                        # Silence timeout reached, process speech
                                        print("DEBUG: Processing speech...")
                                        self._process_speech(speech_buffer)
                                        speech_buffer = []
                                        is_speaking = False
                                        silence_start_time = None
                    except queue.Empty:
                        continue
                        
        except Exception as e:
            msg = f"Audio stream error: {e}"
            print(msg)
            self.error_occurred.emit(msg)

    def _audio_callback(self, indata, frames, time, status):
        """Sounddevice callback."""
        if status:
            print(status)
        self._audio_queue.put(indata.copy())

    def _process_speech(self, valid_frames):
        """Convert frames to AudioData and recognize."""
        if not valid_frames:
            return

        # Concatenate all numpy arrays
        audio_data = np.concatenate(valid_frames)
        
        # Convert to bytes
        audio_bytes = audio_data.tobytes()
        
        # Create SR AudioData
        # width=2 for 16-bit int
        sr_audio = sr.AudioData(audio_bytes, self.sample_rate, 2)
        
        try:
            # Recognize
            text = self._recognizer.recognize_google(sr_audio)
            if text:
                self.text_recognized.emit(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            self.error_occurred.emit(f"API Error: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Recognition Error: {e}")

class VoiceInputManager(QObject):
    """Manager interface."""
    text_recognized = Signal(str)
    listening_started = Signal()
    listening_ended = Signal()
    error_occurred = Signal(str)
    audio_level_changed = Signal(float)
    
    def __init__(self):
        super().__init__()
        self.worker = VoiceInputWorker()
        self.worker.text_recognized.connect(self.text_recognized)
        self.worker.listening_started.connect(self.listening_started)
        self.worker.listening_ended.connect(self.listening_ended)
        self.worker.error_occurred.connect(self.error_occurred)
        self.worker.audio_level_changed.connect(self.audio_level_changed)

    def start_listening(self):
        self.worker.start()

    def stop_listening(self):
        self.worker.stop()
