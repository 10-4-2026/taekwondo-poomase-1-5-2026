import urllib.request
import os

model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
model_path = "pose_landmarker.task"

if not os.path.exists(model_path):
    print(f"Downloading model from {model_url}...")
    urllib.request.urlretrieve(model_url, model_path)
    print("Download complete.")
else:
    print("Model already exists.")
