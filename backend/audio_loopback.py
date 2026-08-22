import sys
from typing import Optional, Dict, Any, List

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False


def list_audio_devices() -> List[Dict[str, Any]]:
    """
    List all input and loopback audio devices available on the system.
    """
    if not SOUNDDEVICE_AVAILABLE:
        return []

    devices = []
    try:
        raw_devices = sd.query_devices()
        host_apis = sd.query_hostapis()
        for idx, dev in enumerate(raw_devices):
            host_api_name = host_apis[dev["hostapi"]]["name"] if dev["hostapi"] < len(host_apis) else "Unknown"
            devices.append({
                "id": idx,
                "name": dev["name"],
                "max_input_channels": dev["max_input_channels"],
                "max_output_channels": dev["max_output_channels"],
                "host_api": host_api_name,
                "default_samplerate": dev["default_samplerate"]
            })
    except Exception as e:
        print(f"[Warning] Failed to query audio devices: {e}")

    return devices


def find_system_loopback_device() -> Optional[int]:
    """
    Auto-detect system audio loopback device (for capturing meeting/speaker audio):
    - Windows: 'Stereo Mix', 'WASAPI Loopback', 'What U Hear'
    - macOS: 'BlackHole', 'Soundflower', 'Multi-Output'
    - Linux: '.monitor' suffix
    """
    if not SOUNDDEVICE_AVAILABLE:
        return None

    try:
        devices = sd.query_devices()
        
        # Priority 1: Check for explicit Stereo Mix / Loopback by name
        preferred_keywords = [
            "stereo mix",
            "what u hear",
            "loopback",
            "blackhole",
            "soundflower",
            "wave out mix",
            "mixed output"
        ]

        for idx, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                name_lower = dev["name"].lower()
                for kw in preferred_keywords:
                    if kw in name_lower:
                        return idx

        # Priority 2: Check for Linux PulseAudio monitor sources
        if sys.platform.startswith("linux"):
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0 and ".monitor" in dev["name"].lower():
                    return idx

        return None
    except Exception as e:
        print(f"[Warning] Error detecting loopback device: {e}")
        return None


def find_default_mic_device() -> Optional[int]:
    """
    Get the default microphone input device index.
    """
    if not SOUNDDEVICE_AVAILABLE:
        return None
    try:
        default_in = sd.default.device[0]
        if default_in is not None and default_in >= 0:
            return default_in
        return None
    except Exception:
        return None
