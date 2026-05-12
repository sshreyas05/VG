import json
import urllib.request

url = "https://satyamashtikar--cinematic-audio-api-serve.modal.run/generate"
payload = {
    "dialogue": " ",
    "music": "",
    "sfx": "",
    "sfx_volume": 1.0,
    "music_volume": 0.5,
    "dialogue_volume": 1.0,
    "total_duration": 5.0,
    "sfx_start": 0.0,
    "dialogue_start": 0.0
}
data = json.dumps(payload).encode("utf-8")
req  = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        print("Status", resp.status)
        print("Response:", resp.read().decode())
except Exception as e:
    print(f"Exception: {e}")
    if hasattr(e, 'read'):
        print("Body:", e.read().decode())
