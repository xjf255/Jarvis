# Workflow de Desarrollo

## Cómo correr el proyecto

```bash
# Activar el entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Correr el asistente
python main.py
```

> ⚠️ Requiere micrófono y altavoces conectados. La primera ejecución descargará los modelos de Whisper y XTTS v2 (varios GB).

## Instalación de dependencias del sistema

### Linux (Ubuntu/Debian)

```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install libportaudio2 vlc python3-pip

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt
```

### Windows (Windows 10+)

1. Instalar Python 3.10+ desde https://python.org (marcar "Add to PATH")
2. Instalar VLC desde https://videolan.org (requerido para reproducción de audio de YouTube)
   - PortAudio está incluido en el wheel de sounddevice en Windows — no se requiere instalación adicional
3. Crear entorno virtual y activar:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

## Plataformas soportadas

| Plataforma | Estado |
|---|---|
| Linux (Ubuntu 22.04+) | ✅ Soportado |
| Windows 10+ | ✅ Soportado |
| macOS | ❌ No soportado |
| Android | ❌ No soportado |
| iOS | ❌ No soportado |

> ⚠️ Android, iOS y macOS no son plataformas objetivo. El proyecto puede no funcionar en ellas.

## Variables de entorno

El archivo `.env` en la raíz del proyecto debe tener el siguiente formato:

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
WAKE_WORD_THRESHOLD=0.5
TTS_SPEED=1.0
```

> ⚠️ El `.env` está en `.gitignore` — nunca commitear claves de API.

## Cómo correr los tests

```bash
# Todos los tests
pytest

# Con verbose
pytest -v

# Solo un módulo
pytest tests/test_llm.py -v
```

## Modelos gratuitos disponibles en OpenRouter

Cualquier modelo con sufijo `:free` funciona. Algunos recomendados para asistente de voz (respuestas cortas y rápidas):

| Modelo | ID para `LLM_MODEL` |
|---|---|
| Llama 3.1 8B (recomendado) | `meta-llama/llama-3.1-8b-instruct:free` |
| Mistral 7B | `mistralai/mistral-7b-instruct:free` |
| Gemma 2 9B | `google/gemma-2-9b-it:free` |
| Qwen 2.5 7B | `qwen/qwen-2.5-7b-instruct:free` |

Ver lista completa en: https://openrouter.ai/models?q=free

## Agregar un nuevo módulo en `app/utils/`

1. Crear `app/utils/<nombre>.py`
2. Definir una función o clase con su docstring completo
3. Importar en `main.py` con `from app.utils.<nombre> import <función>`
4. Actualizar `requirements.txt` si hay nuevas dependencias

## Flujo de git

```bash
# Antes de commitear, verificar que no haya secretos
git diff --staged

# No commitear nunca:
# - .env
# - output.wav
# - __pycache__/
# - *.pyc
```

## Spec del proyecto

El spec completo está en `.kiro/specs/voice-assistant-pipeline/`:
- `requirements.md` — requisitos funcionales
- `design.md` — diseño técnico y propiedades de corrección
- `tasks.md` — tareas de implementación (checklist)

Para implementar las tareas: abrir `tasks.md` y ejecutar cada tarea en orden, verificando los checkpoints antes de continuar.
