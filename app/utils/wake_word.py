from pathlib import Path
import openwakeword
from openwakeword.model import Model

# Descarga los modelos base necesarios (embedding, melspectrogram) 
# la primera vez que se ejecuta. Es una función distinta a la que fallaba antes.
openwakeword.utils.download_models()

# Usa el modelo pre-entrenado "hey_jarvis" que ya incluye la librería
model = Model(
    wakeword_model_paths=["hey_jarvis_v0.1"]
)

def detect_wake_word(audio_data):
    """
    Detecta la palabra de activación "Hey Jarvis" en el audio proporcionado.

    Args:
        audio_data (bytes): Datos de audio en formato PCM 16-bit.

    Returns:
        bool: True si se detecta la palabra de activación, False en caso contrario.
    """
    prediction = model.predict(audio_data)
    # prediction es un diccionario {nombre_modelo: score}
    return prediction.get("hey_jarvis_v0.1", 0) > 0.5