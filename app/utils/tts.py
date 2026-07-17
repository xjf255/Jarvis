import os
import torch
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "true"  # Agree to the terms of service

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Initialize the advanced multi-lingual model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def synthesize_text_to_file(text, speaker_wav, language, file_path, speed=1.0):
    """
    Synthesize text to speech and save it to a file.

    Args:
        text (str): The text to synthesize.
        speaker_wav (str): Path to the speaker's audio sample.
        language (str): Language code for synthesis.
        file_path (str): Path to save the output audio file.
        speed (float): Speed of the synthesized speech.
    """
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language=language,
        file_path=file_path,
        speed=speed
    )