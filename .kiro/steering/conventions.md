# Convenciones de Código

## General

- Python **3.10+**
- Cada módulo en `app/utils/` tiene una única responsabilidad (VAD, STT, TTS, LLM, wake word)
- `main.py` es el único orquestador — no debe contener lógica de procesamiento de audio o texto
- No usar clases innecesarias; preferir funciones puras cuando el módulo no mantiene estado
- Usar clases cuando el módulo gestiona estado o recursos inicializados una sola vez (ej. `LLMClient`)

## Imports

- Imports de stdlib primero, luego third-party, luego locales (`app.utils.*`)
- Imports de módulos locales siempre con ruta absoluta desde la raíz: `from app.utils.stt import transcribe_audio`

## Docstrings

Todos los módulos y funciones públicas deben tener docstring con:
- Descripción en una línea
- Sección `Args:` con tipo y descripción de cada parámetro
- Sección `Returns:` con tipo y descripción del valor de retorno

```python
def transcribe_audio(audio_np: np.ndarray) -> str:
    """
    Transcribe un segmento de audio a texto usando Whisper.

    Args:
        audio_np (np.ndarray): Audio en formato float32 normalizado [-1.0, 1.0].

    Returns:
        str: Texto transcrito.
    """
```

## Tipos

- Anotar tipos en todas las funciones públicas (parámetros y retorno)
- Usar `np.ndarray` para arrays de audio, `bytes` para PCM crudo, `str` para texto

## Constantes de configuración

- Definir constantes de módulo en MAYÚSCULAS al inicio del archivo
- Las constantes de audio van en `vad.py` (son la fuente de verdad para parámetros de audio)

```python
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
```

## Manejo de errores

- Errores irrecuperables en inicialización: lanzar excepción descriptiva o `sys.exit(1)`
- Errores recuperables en el loop principal: capturar con `except Exception as e`, imprimir `[Error] {type(e).__name__}: {e}`, volver al Estado_Inactivo
- No silenciar excepciones con `except: pass`

## Logging

- Usar `print()` para mensajes de estado del pipeline (no `logging` — el proyecto es simple)
- Prefijos de emoji para mensajes de estado:
  - `🎙️` — inicio de captura de voz
  - `🔇` — fin de voz / silencio detectado
  - `🤖` — respuesta del LLM recibida
  - `🔊` — inicio de reproducción
  - `✅` — ciclo completado, listo para siguiente activación
  - `❌` — error recuperable

## Variables de entorno

- Siempre leer con `os.getenv("NOMBRE", "default")` — nunca hardcodear valores de configuración
- Cargar `.env` con `load_dotenv()` al inicio de `main.py`, antes de inicializar cualquier módulo
- Nunca incluir `OPENROUTER_API_KEY` ni ninguna clave de API en el código fuente

## Tests

- Directorio: `tests/` en la raíz del proyecto
- Framework: `pytest`
- Property-based testing: `hypothesis` con `@settings(max_examples=100)`
- Mockear todas las dependencias externas (API de OpenRouter, sounddevice, modelos de ML)
- Nombrar tests: `test_<módulo>_<comportamiento>.py`
