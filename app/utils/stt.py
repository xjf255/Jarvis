import whisper
model = whisper.load_model("base")

def transcribe_audio(audio_path):
    """
    Transcribe audio from a file using the Whisper model.

    Args:
        audio_path (str): Path to the audio file.
    """
    result = model.transcribe(audio_path, initial_prompt="El usuario está hablando con su asistente virtual llamado Jarvis, Cortana o Viernes.")
    return result["text"] 