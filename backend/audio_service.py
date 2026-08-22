import io
import time
import queue
import threading
from typing import Callable, Optional, Dict, Any, List
import numpy as np
import scipy.io.wavfile as wav

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception as e:
    print(f"[Warning] sounddevice not available: {e}")
    SOUNDDEVICE_AVAILABLE = False

from audio_loopback import find_system_loopback_device, find_default_mic_device, list_audio_devices


class AudioStreamWorker:
    """
    Generic single-source audio capture worker with RMS Voice Activity Detection (VAD).
    Can capture from microphone or system loopback device.
    """
    def __init__(
        self,
        source_label: str = "you",
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        energy_threshold: float = 0.016,
        silence_duration: float = 1.8,
        max_duration: float = 30.0
    ):
        self.source_label = source_label  # "you" or "colleague"
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration

        self.is_recording = False
        self.stream = None
        self.audio_thread = None
        self.audio_queue = queue.Queue()
        self.on_speech_chunk_callback: Optional[Callable[[bytes, str], None]] = None

        # VAD State
        self.recording_buffer = []
        self.is_speaking = False
        self.silence_start_time = None
        self.speech_start_time = None

    def set_on_speech_callback(self, callback: Callable[[bytes, str], None]):
        self.on_speech_chunk_callback = callback

    def update_settings(self, silence_duration: Optional[float] = None, energy_threshold: Optional[float] = None):
        if silence_duration is not None:
            self.silence_duration = max(0.8, min(4.0, float(silence_duration)))
        if energy_threshold is not None:
            self.energy_threshold = max(0.003, min(0.08, float(energy_threshold)))

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass  # Suppress routine buffer underflow notices
        # If stereo or multichannel, convert to mono float32
        if indata.ndim > 1 and indata.shape[1] > 1:
            mono = np.mean(indata, axis=1, keepdims=True)
            self.audio_queue.put(mono.copy())
        else:
            self.audio_queue.put(indata.copy())

    def start(self) -> Dict[str, Any]:
        if not SOUNDDEVICE_AVAILABLE:
            return {"success": False, "error": "sounddevice library not available"}

        if self.is_recording:
            return {"success": True, "message": f"{self.source_label} already listening"}

        try:
            self.is_recording = True
            self.audio_queue = queue.Queue()
            self.recording_buffer = []
            self.is_speaking = False
            self.silence_start_time = None
            self.speech_start_time = None

            # Query device info for channel support
            channels = 1
            if self.device_index is not None:
                try:
                    dev_info = sd.query_devices(self.device_index)
                    channels = min(2, max(1, dev_info.get("max_input_channels", 1)))
                except Exception:
                    channels = 1

            self.stream = sd.InputStream(
                device=self.device_index,
                samplerate=self.sample_rate,
                channels=channels,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
            )
            self.stream.start()

            self.audio_thread = threading.Thread(target=self._process_audio_stream, daemon=True)
            self.audio_thread.start()

            return {
                "success": True,
                "message": f"Listening started for {self.source_label} (Device {self.device_index})"
            }
        except Exception as e:
            self.is_recording = False
            return {"success": False, "error": str(e)}

    def stop(self) -> Dict[str, Any]:
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        return {"success": True, "message": f"Listening stopped for {self.source_label}"}

    def _process_audio_stream(self):
        while self.is_recording:
            try:
                chunk = self.audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

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

                    if silence_elapsed >= self.silence_duration or speech_duration >= self.max_duration:
                        self.is_speaking = False
                        self.silence_start_time = None
                        self.speech_start_time = None

                        total_frames = sum(len(c) for c in self.recording_buffer)
                        if total_frames >= self.sample_rate * 0.8:
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
                self.on_speech_chunk_callback(wav_bytes, self.source_label)
            except Exception as e:
                print(f"[Error in {self.source_label} speech callback]: {e}")


class DualAudioCaptureService:
    """
    Manager coordinating both Microphone (You) and System Audio Loopback (Colleagues / Meeting Audio).
    Emits speech callbacks with source tagging ("you" vs "colleague").
    """
    def __init__(self, sample_rate: int = 16000, silence_duration: float = 1.8, energy_threshold: float = 0.016):
        self.sample_rate = sample_rate
        self.silence_duration = silence_duration
        self.energy_threshold = energy_threshold

        self.on_speech_callback: Optional[Callable[[bytes, str], None]] = None

        # Workers
        self.mic_worker: Optional[AudioStreamWorker] = None
        self.loopback_worker: Optional[AudioStreamWorker] = None

        self.is_listening = False
        self.loopback_enabled = True

    def set_on_speech_callback(self, callback: Callable[[bytes, str], None]):
        self.on_speech_callback = callback
        if self.mic_worker:
            self.mic_worker.set_on_speech_callback(callback)
        if self.loopback_worker:
            self.loopback_worker.set_on_speech_callback(callback)

    def update_settings(self, silence_duration: Optional[float] = None, energy_threshold: Optional[float] = None, loopback_enabled: Optional[bool] = None):
        if silence_duration is not None:
            self.silence_duration = silence_duration
            if self.mic_worker:
                self.mic_worker.update_settings(silence_duration=silence_duration)
            if self.loopback_worker:
                self.loopback_worker.update_settings(silence_duration=silence_duration)

        if energy_threshold is not None:
            self.energy_threshold = energy_threshold
            if self.mic_worker:
                self.mic_worker.update_settings(energy_threshold=energy_threshold)
            if self.loopback_worker:
                # System audio is slightly lower energy
                self.loopback_worker.update_settings(energy_threshold=energy_threshold * 0.7)

        if loopback_enabled is not None:
            self.loopback_enabled = loopback_enabled

    def start_listening(self) -> Dict[str, Any]:
        if not SOUNDDEVICE_AVAILABLE:
            return {"success": False, "error": "sounddevice library is not available"}

        if self.is_listening:
            return {"success": True, "message": "Already listening"}

        self.is_listening = True

        # 1. Microphone Worker (You)
        mic_dev = find_default_mic_device()
        self.mic_worker = AudioStreamWorker(
            source_label="you",
            device_index=mic_dev,
            sample_rate=self.sample_rate,
            energy_threshold=self.energy_threshold,
            silence_duration=self.silence_duration
        )
        if self.on_speech_callback:
            self.mic_worker.set_on_speech_callback(self.on_speech_callback)
        mic_res = self.mic_worker.start()

        # 2. System Audio Loopback Worker (Colleague / Meeting Audio)
        loopback_msg = "Loopback disabled"
        loopback_dev = find_system_loopback_device() if self.loopback_enabled else None
        if loopback_dev is not None and loopback_dev != mic_dev:
            self.loopback_worker = AudioStreamWorker(
                source_label="colleague",
                device_index=loopback_dev,
                sample_rate=self.sample_rate,
                energy_threshold=self.energy_threshold * 0.7,  # slightly more sensitive for meeting audio
                silence_duration=self.silence_duration
            )
            if self.on_speech_callback:
                self.loopback_worker.set_on_speech_callback(self.on_speech_callback)
            loop_res = self.loopback_worker.start()
            loopback_msg = f"System audio active (Device {loopback_dev})"
        else:
            self.loopback_worker = None
            loopback_msg = "No separate loopback device detected (Mic only active)"

        return {
            "success": True,
            "message": f"Dual audio capture running. {loopback_msg}",
            "silence_duration": self.silence_duration,
            "loopback_active": self.loopback_worker is not None
        }

    def stop_listening(self) -> Dict[str, Any]:
        self.is_listening = False
        if self.mic_worker:
            self.mic_worker.stop()
            self.mic_worker = None
        if self.loopback_worker:
            self.loopback_worker.stop()
            self.loopback_worker = None
        return {"success": True, "message": "Dual audio listening stopped"}

    @staticmethod
    def convert_pcm_bytes_to_wav(pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
        wav_io = io.BytesIO()
        audio_array = np.frombuffer(pcm_bytes, dtype=np.int16)
        wav.write(wav_io, sample_rate, audio_array)
        return wav_io.getvalue()
