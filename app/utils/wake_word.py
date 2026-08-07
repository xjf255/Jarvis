from pathlib import Path
import openwakeword 
from openwakeword.model import Model

MODEL_DIR = Path("app") / "resources" / "wakeword_models"

# En la versión 0.4.0, los modelos se descargan automáticamente
# al crear el Model() si no existen localmente — no se llama manualmente
model = Model(
    wakeword_model_paths=[str(MODEL_DIR / "hey_jarvis_v0.1.onnx")]
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
    return prediction.get("hey_jarvis_v0.1", 0) > 0.5 # type: ignore