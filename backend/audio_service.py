import io
import time
import queue
import threading
import numpy as np
import scipy.io.wavfile as wav
from typing import Callable, Optional, Dict, Any

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception as e:
    print(f"[Warning] sounddevice not available: {e}")
    SOUNDDEVICE_AVAILABLE = False


class AudioCaptureService:
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.016, silence_duration: float = 1.8, max_duration: float = 30.0):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration
        
        self.is_recording = False
        self.stream = None
        self.audio_thread = None
        
        self.audio_queue = queue.Queue()
        self.on_speech_chunk_callback: Optional[Callable[[bytes], None]] = None
        
        # VAD State
        self.recording_buffer = []
        self.is_speaking = False
        self.silence_start_time = None
        self.speech_start_time = None

    def set_on_speech_callback(self, callback: Callable[[bytes], None]):
        self.on_speech_chunk_callback = callback

    def update_settings(self, silence_duration: Optional[float] = None, energy_threshold: Optional[float] = None):
        if silence_duration is not None:
            self.silence_duration = max(0.8, min(4.0, float(silence_duration)))
        if energy_threshold is not None:
            self.energy_threshold = max(0.005, min(0.08, float(energy_threshold)))

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[Audio Status Warning]: {status}")
        self.audio_queue.put(indata.copy())

    def start_listening(self) -> Dict[str, Any]:
        if not SOUNDDEVICE_AVAILABLE:
            return {"success": False, "error": "sounddevice library is not available on this system"}
        
        if self.is_recording:
            return {"success": True, "message": "Already listening"}

        try:
            self.is_recording = True
            self.audio_queue = queue.Queue()
            self.recording_buffer = []
            self.is_speaking = False
            self.silence_start_time = None
            self.speech_start_time = None
            
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1) # 100ms blocks
            )
            self.stream.start()

            self.audio_thread = threading.Thread(target=self._process_audio_stream, daemon=True)
            self.audio_thread.start()

            return {
                "success": True,
                "message": f"Microphone listening started (Pause duration: {self.silence_duration}s)",
                "silence_duration": self.silence_duration
            }
        except Exception as e:
            self.is_recording = False
            return {"success": False, "error": str(e)}

    def stop_listening(self) -> Dict[str, Any]:
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        return {"success": True, "message": "Microphone listening stopped"}

    def _process_audio_stream(self):
        while self.is_recording:
            try:
                chunk = self.audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            # Calculate RMS energy for VAD
            rms = np.sqrt(np.mean(chunk**2))
            now = time.time()

            if rms > self.energy_threshold:
                if not self.is_speaking:
                    self.is_speaking = True
                    self.speech_start_time = now
                    self.recording_buffer = []
                self.silence_start_time = None
                self.recording_buffer.append(chunk)
            else:
                if self.is_speaking:
                    self.recording_buffer.append(chunk)
                    if self.silence_start_time is None:
                        self.silence_start_time = now
                    
                    speech_duration = now - (self.speech_start_time or now)
                    silence_elapsed = now - self.silence_start_time

                    # Trigger if silence exceeds configured duration OR max speech length reached
                    if silence_elapsed >= self.silence_duration or speech_duration >= self.max_duration:
                        self.is_speaking = False
                        self.silence_start_time = None
                        self.speech_start_time = None
                        
                        # Only trigger if audio has at least ~0.8s of speech
                        total_frames = sum(len(c) for c in self.recording_buffer)
                        if total_frames >= self.sample_rate * 0.8:
                            # Verify that the entire buffer had meaningful voice energy (not just a single click)
                            full_arr = np.concatenate(self.recording_buffer, axis=0)
                            buf_rms = np.sqrt(np.mean(full_arr**2))
                            if buf_rms >= self.energy_threshold * 0.7:
                                self._trigger_speech_callback(self.recording_buffer)
                        self.recording_buffer = []

    def _trigger_speech_callback(self, buffer_chunks):
        if not buffer_chunks:
            return
        
        full_audio = np.concatenate(buffer_chunks, axis=0)
        audio_int16 = np.int16(full_audio * 32767)
        
        wav_io = io.BytesIO()
        wav.write(wav_io, self.sample_rate, audio_int16)
        wav_bytes = wav_io.getvalue()

        if self.on_speech_chunk_callback:
            try:
                self.on_speech_chunk_callback(wav_bytes)
            except Exception as e:
                print(f"[Error in speech callback]: {e}")

    @staticmethod
    def convert_pcm_bytes_to_wav(pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
        wav_io = io.BytesIO()
        audio_array = np.frombuffer(pcm_bytes, dtype=np.int16)
        wav.write(wav_io, sample_rate, audio_array)
        return wav_io.getvalue()
