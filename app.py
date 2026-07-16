import os
import torch
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "true"  # Agree to the terms of service

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize the advanced multi-lingual model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# Synthesize text and export directly to a local .wav file
tts.tts_to_file(
    text="Hello world! This is an advanced PyTorch speech synthesis network.", 
    speaker_wav="./app/resources/audio.wav", # Audio sample to copy voice from
    language="en", 
    file_path="output.wav"
)
