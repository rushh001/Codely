import sounddevice as sd

print("All sound devices:")
devices = sd.query_devices()
for i, d in enumerate(devices):
    print(f"[{i}] {d['name']} (In: {d['max_input_channels']}, Out: {d['max_output_channels']}, HostAPI: {d['hostapi']})")

print("\nHost APIs:")
for i, api in enumerate(sd.query_hostapis()):
    print(f"[{i}] {api['name']}")
