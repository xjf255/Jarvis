import openwakeword 
from openwakeword.model import Model

openwakeword.utils.download_models()

model = Model(
    wakeword_models=["app/resources/jarvis_model.zip"]
)

def detect_wake_word(audio_data):
    """
    Detecta la palabra de activación en el audio proporcionado.

    Args:
        audio_data (bytes): Datos de audio en formato PCM 16-bit.

    Returns:
        bool: True si se detecta la palabra de activación, False en caso contrario.
    """
    return model.predict(audio_data)