# Implementation Plan: Voice Assistant Pipeline

## Overview

Este plan conecta todos los módulos existentes (VAD, STT, TTS, wake word) en un pipeline de voz completo, añadiendo el módulo LLM con OpenRouter y refactorizando `main.py` como orquestador. Adicionalmente incorpora el Sistema de Herramientas: `ToolDispatcher`, `YouTubeTool`, `WhatsAppTool` y `BrowserTool`. El lenguaje de implementación es **Python**.

---

## Tasks

- [x] 1. Configuración del entorno y dependencias
  - Añadir a `requirements.txt` las dependencias: `openai`, `python-dotenv`, `pytest`, `hypothesis`, `openwakeword`
  - Verificar que el archivo `.env` contiene al menos el campo `OPENROUTER_API_KEY`
  - **Linux**: verificar que `libportaudio2` y `vlc` estén instalados (`sudo apt install libportaudio2 vlc`)
  - **Windows**: verificar que VLC esté instalado desde https://videolan.org; PortAudio está incluido en el wheel de sounddevice
  - _Requisitos: 2.1, 2.2, 8.1, 8.3_

- [x] 2. Implementar el módulo LLMClient
  - [x] 2.1 Crear `app/utils/llm.py` con la clase `LLMClient`
    - Implementar `__init__`: leer `OPENROUTER_API_KEY` y `LLM_MODEL` del entorno con `os.getenv`; lanzar `ValueError` si la clave está ausente; configurar `openai.OpenAI(api_key=..., base_url="https://openrouter.ai/api/v1")`
    - Definir la constante `SYSTEM_PROMPT` con las instrucciones de respuesta concisa en español sin markdown
    - Implementar `generate(self, user_text: str) -> str`: construir la lista de mensajes con el system prompt y el mensaje del usuario; llamar a `client.chat.completions.create` con `max_tokens=300`; retornar `response.choices[0].message.content`
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

  - [ ]* 2.2 Escribir pruebas unitarias de ejemplo para LLMClient
    - Probar que `__init__` lanza `ValueError` cuando `OPENROUTER_API_KEY` no está definida
    - Probar que el modelo por defecto es `meta-llama/llama-3.1-8b-instruct:free` cuando `LLM_MODEL` no está en el entorno
    - Probar que `base_url` del cliente apunta a `https://openrouter.ai/api/v1`
    - Probar que las excepciones de la API se propagan sin atrapar
    - _Requisitos: 1.1, 1.2, 1.3, 1.8, 1.9_

  - [ ]* 2.3 Escribir prueba de propiedad: el payload incluye siempre el texto del usuario
    - **Propiedad 1: El payload de la solicitud LLM incluye siempre el mensaje del usuario**
    - Usar `hypothesis` con estrategia `st.text(min_size=1)` para generar consultas arbitrarias
    - Mockear `openai.OpenAI` para capturar los argumentos pasados a `chat.completions.create`
    - Verificar que `messages[-1]["role"] == "user"` y `messages[-1]["content"] == user_text`
    - Mínimo 100 iteraciones (`settings(max_examples=100)`)
    - _Feature: voice-assistant-pipeline, Propiedad 1: El payload de la solicitud LLM incluye siempre el mensaje del usuario_
    - _Requisitos: 1.4_

  - [ ]* 2.4 Escribir prueba de propiedad: extracción correcta del texto de respuesta
    - **Propiedad 2: Extracción correcta del texto de respuesta del LLM**
    - Usar `hypothesis` con estrategia `st.text()` para generar textos de respuesta arbitrarios (incluyendo Unicode, caracteres especiales, saltos de línea)
    - Construir un mock de la respuesta de la API con ese texto en `choices[0].message.content` y `finish_reason != "tool_calls"`
    - Verificar que `generate()` retorna un `LLMResponse(type="text")` con `text` igual al contenido sin modificación
    - Mínimo 100 iteraciones
    - _Feature: voice-assistant-pipeline, Propiedad 2: Extracción correcta del texto de respuesta del LLM_
    - _Requisitos: 1.7, 7.3_

- [x] 3. Checkpoint — Verificar módulo LLM
  - Ejecutar `pytest` sobre las pruebas de `llm.py`. Asegurarse de que todas pasan antes de continuar. Consultar al usuario si hay dudas.

- [x] 4. Refactorizar `main.py` como Pipeline_Controller
  - [x] 4.1 Añadir carga de configuración con `python-dotenv`
    - Al inicio de `main.py`, importar `dotenv` y llamar a `load_dotenv()`
    - Leer `WAKE_WORD_THRESHOLD` (float, default `0.5`) y `TTS_SPEED` (float, default `1.0`) con `os.getenv`
    - Instanciar `LLMClient`; si lanza `ValueError`, imprimir el error y salir con `sys.exit(1)`
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 4.2 Implementar el enum `PipelineState` y el bucle de wake word
    - Definir `PipelineState(Enum)` con los cuatro estados: `INACTIVE`, `LISTENING`, `PROCESSING`, `RESPONDING`
    - Implementar la función `run_pipeline()` con un `RawInputStream` de sounddevice a 16000 Hz, canales=1, dtype=int16
    - En el bucle de wake word, acumular frames de **1280 muestras** y llamar a `detect_wake_word(frame)`; extraer la puntuación del modelo y comparar con `WAKE_WORD_THRESHOLD`
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 4.3 Implementar la transición Estado_Escuchando → Estado_Procesando
    - Cuando se detecta el wake word, imprimir mensaje de activación y cambiar estado a `LISTENING`
    - Llamar a `vad_collector` para capturar el segmento PCM del usuario
    - Convertir el PCM a `np.float32` y llamar a `transcribe_audio(audio_np)`
    - Si la transcripción es vacía o solo espacios en blanco (`transcripcion.strip() == ""`), imprimir aviso y volver a `INACTIVE`
    - En caso contrario, imprimir la transcripción y continuar al Estado_Procesando
    - _Requisitos: 4.1, 4.2, 4.3, 4.9, 6.3_

  - [x] 4.4 Implementar Estado_Procesando: LLM + TTS
    - Llamar a `llm_client.generate(transcripcion)`, imprimir la respuesta
    - Llamar a `synthesize_text_to_file(respuesta, "app/resources/audio.wav", "es", "output.wav", speed=TTS_SPEED)`
    - Cambiar estado a `RESPONDING`
    - _Requisitos: 4.4, 4.5, 4.8, 6.4_

  - [x] 4.5 Implementar Estado_Respondiendo: reproducción de audio
    - Leer `output.wav` con `soundfile.read` y reproducirlo con `sounddevice.play` + `sounddevice.wait`
    - Al finalizar, cambiar estado a `INACTIVE` e imprimir mensaje de disponibilidad
    - _Requisitos: 4.6, 4.7, 6.5_

  - [x] 4.6 Implementar manejo de errores recuperables y `KeyboardInterrupt`
    - Envolver los pasos de LLM, TTS y reproducción en un bloque `try/except Exception as e`; en el `except`, imprimir `[Error recuperable] {type(e).__name__}: {e}` y volver a `INACTIVE`
    - Envolver el bucle principal en `try/except KeyboardInterrupt`; en el `except`, imprimir mensaje de cierre y liberar recursos de audio
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 2.5 Escribir prueba de propiedad: transcripciones de solo espacios en blanco son descartadas
    - **Propiedad 3: Transcripciones vacías o de solo espacios en blanco son descartadas**
    - Usar `hypothesis` con estrategia `st.text(alphabet=st.characters(whitespace=True, blacklist_categories=('L','N','P','S')))` o `st.from_regex(r'\s*')` para generar cadenas de solo espacios en blanco
    - Mockear `LLMClient.generate` y `synthesize_text_to_file` para detectar si son llamados
    - Verificar que cuando `transcribe_audio` retorna la cadena generada, ni `generate` ni `synthesize_text_to_file` son invocados
    - Mínimo 100 iteraciones
    - _Feature: voice-assistant-pipeline, Propiedad 3: Transcripciones vacías o de solo espacios en blanco son descartadas_
    - _Requisitos: 4.9_

  - [ ]* 2.6 Escribir prueba de propiedad: umbral de wake word separa activaciones correctamente
    - **Propiedad 4: El umbral de wake word separa correctamente activaciones de no-activaciones**
    - Usar `hypothesis` con estrategias `st.floats(min_value=0.0, max_value=1.0)` para la puntuación y el umbral
    - Mockear `detect_wake_word` para retornar la puntuación generada
    - Verificar que el pipeline transiciona a `LISTENING` si y solo si `score >= threshold`
    - Mínimo 100 iteraciones
    - _Feature: voice-assistant-pipeline, Propiedad 4: El umbral de wake word separa correctamente activaciones de no-activaciones_
    - _Requisitos: 3.2_

- [x] 5. Checkpoint — Verificar pipeline completo
  - Ejecutar todos los tests (`pytest`). Asegurarse de que todas las pruebas pasan. Consultar al usuario si hay dudas.

- [x] 6. Conectar `main.py` con el punto de entrada
  - Asegurarse de que `main.py` llama a `run_pipeline()` bajo el bloque `if __name__ == "__main__":`
  - Eliminar o comentar el código anterior de `vad_main()` que ya no aplica
  - Imprimir el mensaje de inicio del sistema indicando que espera la palabra de activación
  - _Requisitos: 6.1_

  - [ ]* 6.1 Escribir pruebas de integración del pipeline con mocks
    - Mockear `detect_wake_word`, `transcribe_audio`, `LLMClient.generate`, `synthesize_text_to_file` y `sounddevice`
    - Verificar el flujo completo: wake word → transcripción → LLM → TTS → reproducción → Estado_Inactivo
    - Verificar que los mensajes de consola se imprimen en el orden correcto en cada transición de estado
    - Verificar que un error en `generate()` no termina el proceso y devuelve al Estado_Inactivo
    - _Requisitos: 4.1–4.8, 5.1–5.3, 6.1–6.5_

- [x] 7. Checkpoint final — Verificar todo el sistema base
  - Ejecutar todos los tests (`pytest`). Asegurarse de que todas las pruebas pasan. Consultar al usuario si hay dudas.

- [x] 8. Actualizar dependencias para el Sistema de Herramientas
  - Añadir a `requirements.txt`: `yt-dlp`, `python-vlc`, `pywhatkit`
  - Crear el directorio `app/tools/` con un archivo `__init__.py` vacío
  - _Requisitos: 7.1, 7.2, 7.3_

- [x] 9. Implementar LLMClient con soporte de function calling
  - [x] 9.1 Actualizar `app/utils/llm.py`: añadir `LLMResponse` y definiciones de herramientas
    - Definir el dataclass `LLMResponse` con campos `type`, `text`, `tool_name`, `tool_args`
    - Definir la constante `TOOL_DEFINITIONS` con las tres herramientas (youtube, whatsapp, browser) en formato OpenAI function calling
    - Actualizar el `SYSTEM_PROMPT` para incluir instrucciones sobre el uso de herramientas
    - _Requisitos: 7.1, 7.2, 7.3_

  - [x] 9.2 Actualizar `LLMClient.generate()` para retornar `LLMResponse`
    - Pasar `tools=TOOL_DEFINITIONS` y `tool_choice="auto"` a `chat.completions.create`
    - Si `choice.finish_reason == "tool_calls"` y `choice.message.tool_calls` no está vacío, parsear el `tool_call` con `json.loads` y retornar `LLMResponse(type="tool_call", ...)`
    - En caso contrario, retornar `LLMResponse(type="text", text=choice.message.content)`
    - _Requisitos: 7.1, 7.2, 7.3_

  - [ ]* 9.3 Escribir prueba de propiedad: clasificación correcta de respuesta según finish_reason
    - **Propiedad 6: El LLMClient clasifica correctamente la respuesta según finish_reason**
    - Usar `hypothesis` para generar textos de respuesta arbitrarios con `finish_reason != "tool_calls"`
    - Verificar que `generate()` retorna siempre `LLMResponse(type="text")` en ese caso
    - Usar `hypothesis` para generar tool_calls con `finish_reason == "tool_calls"`
    - Verificar que `generate()` retorna siempre `LLMResponse(type="tool_call")` en ese caso
    - Mínimo 100 iteraciones por caso
    - _Feature: voice-assistant-pipeline, Propiedad 6: El LLMClient clasifica correctamente la respuesta según finish_reason_
    - _Requisitos: 7.2, 7.3_

- [x] 10. Implementar BrowserTool
  - [x] 10.1 Crear `app/tools/browser.py` con la clase `BrowserTool`
    - Implementar `execute(action, query="", url="")` que despacha a `_search()` o `_open_url()`
    - `_search(query)`: construir URL de Google con `urllib.parse.quote_plus(query)` y abrir con `webbrowser.open()`; retornar string de confirmación
    - `_open_url(url)`: si `url` no comienza con `"http://"` ni `"https://"`, añadir `"https://"`; abrir con `webbrowser.open()`; retornar string de confirmación
    - Capturar excepciones y retornar string de error descriptivo en caso de fallo
    - _Requisitos: 7.3.1, 7.3.2, 7.3.3, 7.3.4, 7.3.5_

  - [ ]* 10.2 Escribir prueba de propiedad: normalización de URLs sin esquema
    - **Propiedad 7: El BrowserTool normaliza URLs sin esquema**
    - Usar `hypothesis` con estrategia `st.text(min_size=1)` filtrando strings que no comiencen con `"http://"` ni `"https://"`
    - Mockear `webbrowser.open` para capturar la URL final
    - Verificar que la URL abierta siempre comienza con `"https://"`
    - Mínimo 100 iteraciones
    - _Feature: voice-assistant-pipeline, Propiedad 7: El BrowserTool normaliza URLs sin esquema_
    - _Requisitos: 7.3.4_

  - [ ]* 10.3 Escribir pruebas unitarias de ejemplo para BrowserTool
    - Probar que `_search("clima hoy")` construye correctamente la URL de Google
    - Probar que `_open_url("https://youtube.com")` abre sin modificar la URL
    - Probar que `_open_url("youtube.com")` añade el prefijo `"https://"`
    - Probar que una excepción de `webbrowser.open` retorna string de error, no lanza
    - _Requisitos: 7.3.1, 7.3.2, 7.3.4, 7.3.5_

- [x] 11. Implementar YouTubeTool
  - [x] 11.1 Crear `app/tools/youtube.py` con la clase `YouTubeTool`
    - Definir `__init__`: inicializar `self._player = None` y `self._current_title = ""`
    - Implementar `execute(action, query="")` que despacha a los métodos privados según `action`
    - Implementar `_play_audio(query)`: usar `yt_dlp.YoutubeDL` con `ytsearch1:{query}`, extraer la URL del stream de audio, crear un `vlc.MediaPlayer` con la URL y llamar a `player.play()`; guardar el título en `self._current_title`
    - Implementar `_play_video(query)`: buscar con yt-dlp y abrir la URL de YouTube en el navegador con `webbrowser.open()`
    - Implementar `_pause()`, `_resume()`, `_stop()` usando métodos del `vlc.MediaPlayer` activo
    - Retornar strings de confirmación descriptivos incluyendo el título del contenido
    - _Requisitos: 7.1.1, 7.1.2, 7.1.3, 7.1.4, 7.1.5, 7.1.6, 7.1.7, 7.1.8_

  - [ ]* 11.2 Escribir pruebas unitarias de ejemplo para YouTubeTool
    - Mockear `yt_dlp.YoutubeDL` para simular resultados de búsqueda
    - Mockear `vlc.MediaPlayer` para verificar que se llama a `play()`, `pause()`, `resume()`, `stop()`
    - Probar que cuando yt-dlp no retorna resultados, se retorna string de "no encontrado"
    - Probar que `_pause()` cuando no hay reproducción activa retorna mensaje apropiado
    - _Requisitos: 7.1.3, 7.1.4, 7.1.5, 7.1.6, 7.1.7, 7.1.8_

- [x] 12. Implementar WhatsAppTool
  - [x] 12.1 Crear `app/tools/whatsapp.py` con la clase `WhatsAppTool`
    - Implementar `execute(action, contact="", message="")` que despacha a `_read_unread()` o `_send_message(contact, message)`
    - Implementar `_send_message(contact, message)`: usar `pywhatkit.sendwhatmsg_instantly()` para enviar el mensaje; retornar string de confirmación
    - Implementar `_read_unread()`: retornar mensaje indicando que la lectura de WhatsApp Web requiere sesión activa (implementación básica con `webbrowser.open("https://web.whatsapp.com")`)
    - Capturar excepciones y retornar strings de error descriptivos
    - _Requisitos: 7.2.1, 7.2.2, 7.2.3, 7.2.4, 7.2.5_

  - [ ]* 12.2 Escribir pruebas unitarias de ejemplo para WhatsAppTool
    - Mockear `pywhatkit.sendwhatmsg_instantly` para verificar que se llama con los parámetros correctos
    - Probar que una excepción de pywhatkit retorna string de error, no lanza
    - _Requisitos: 7.2.2, 7.2.3, 7.2.5_

- [x] 13. Implementar ToolDispatcher
  - [x] 13.1 Crear `app/utils/tool_dispatcher.py` con la clase `ToolDispatcher`
    - Importar `YouTubeTool`, `WhatsAppTool`, `BrowserTool`
    - En `__init__`: instanciar las tres herramientas y construir el registro `self._registry = {"youtube": youtube_tool.execute, "whatsapp": whatsapp_tool.execute, "browser": browser_tool.execute}`
    - Implementar `dispatch(tool_name, tool_args)`: buscar en `self._registry`; si existe, llamar con `**tool_args`; si no existe, retornar mensaje de herramienta no disponible; envolver la llamada en `try/except` para capturar errores de ejecución y retornar string de error descriptivo
    - Garantizar que `dispatch` SIEMPRE retorna un string, nunca lanza excepción
    - _Requisitos: 7.4, 7.5, 7.6, 7.7_

  - [ ]* 13.2 Escribir prueba de propiedad: ToolDispatcher siempre retorna string
    - **Propiedad 5: El ToolDispatcher siempre retorna un string**
    - Usar `hypothesis` para generar nombres de herramienta arbitrarios (incluyendo cadenas vacías y nombres inválidos) y diccionarios de argumentos arbitrarios
    - Verificar que `dispatch()` retorna siempre un `str` no vacío, nunca lanza excepción
    - Mínimo 100 iteraciones
    - _Feature: voice-assistant-pipeline, Propiedad 5: El ToolDispatcher siempre retorna un string_
    - _Requisitos: 7.5, 7.6, 7.7_

  - [ ]* 13.3 Escribir pruebas unitarias de ejemplo para ToolDispatcher
    - Probar que un nombre de herramienta desconocido retorna mensaje de herramienta no disponible
    - Probar que una excepción lanzada por una herramienta es capturada y retorna string de error
    - Probar que las tres herramientas registradas son invocadas correctamente con sus argumentos
    - _Requisitos: 7.5, 7.6, 7.7_

- [x] 14. Checkpoint — Verificar herramientas y dispatcher
  - Ejecutar `pytest` sobre los tests de `browser.py`, `youtube.py`, `whatsapp.py` y `tool_dispatcher.py`. Asegurarse de que todas las pruebas pasan. Consultar al usuario si hay dudas.

- [x] 15. Integrar ToolDispatcher en Pipeline_Controller
  - [x] 15.1 Actualizar `main.py` para instanciar `ToolDispatcher` e integrar la bifurcación post-LLM
    - Importar `ToolDispatcher` desde `app/utils/tool_dispatcher`
    - En `run_pipeline()`: instanciar `tool_dispatcher = ToolDispatcher()`
    - Reemplazar el uso directo de `llm_client.generate()` por la lógica de bifurcación: si `response.type == "text"`, usar `response.text`; si `response.type == "tool_call"`, llamar a `tool_dispatcher.dispatch(response.tool_name, response.tool_args or {})`
    - El string resultante (texto o confirmación de herramienta) se pasa siempre a `synthesize_text_to_file`
    - _Requisitos: 7.4, 7.5, 7.6_

  - [ ]* 15.2 Escribir pruebas de integración del pipeline con herramientas (mocks)
    - Mockear `LLMClient.generate` para retornar `LLMResponse(type="tool_call", tool_name="browser", tool_args={"action": "search", "query": "clima"})`
    - Mockear `ToolDispatcher.dispatch` para retornar `"Buscando clima en Google"`
    - Verificar que el string de confirmación llega a `synthesize_text_to_file`
    - Repetir para `youtube` y `whatsapp`
    - Verificar que un error en `ToolDispatcher.dispatch` no termina el proceso
    - _Requisitos: 7.4, 7.5, 7.6, 5.1_

- [x] 16. Checkpoint final — Verificar sistema completo con herramientas
  - Ejecutar todos los tests (`pytest`). Asegurarse de que todas las pruebas pasan. Consultar al usuario si hay dudas.

- [x] 17. Validar compatibilidad multiplataforma
  - [x] 17.1 Revisar todas las rutas de archivo en el código fuente y reemplazar strings hardcodeados por `pathlib.Path`
    - Buscar todos los usos de `"app/resources/audio.wav"`, `"output.wav"` y similares
    - Reemplazar con `Path("app") / "resources" / "audio.wav"` y `Path("output.wav")`
    - _Requisitos: 8.2_

  - [x] 17.2 Añadir detección de VLC en YouTubeTool
    - En `YouTubeTool.__init__()`, envolver `import vlc` en un `try/except ImportError`
    - Si falla, establecer `self._vlc_available = False` e imprimir un mensaje indicando que VLC no está instalado
    - En `_play_audio()`, verificar `self._vlc_available` antes de intentar reproducir; si es False, retornar string de error
    - _Requisitos: 8.4_

  - [x] 17.3 Documentar instalación por plataforma en `workflow.md` del steering
    - Añadir sección "Instalación en Linux" y "Instalación en Windows" con los pasos de dependencias del sistema
    - _Requisitos: 8.5_

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para una implementación MVP más rápida.
- Cada tarea referencia requisitos específicos para trazabilidad.
- Los checkpoints garantizan validación incremental en cada etapa.
- Las pruebas de propiedad validan corrección universal; las pruebas unitarias validan ejemplos concretos y casos límite.
- Los mocks de `openai.OpenAI` permiten ejecutar las pruebas sin necesidad de una clave de API real.
- `BrowserTool` no requiere dependencias externas adicionales (usa `webbrowser` y `urllib.parse` de la librería estándar).
- `WhatsAppTool` con `pywhatkit` requiere que WhatsApp Web esté autenticado en el navegador por defecto.
- `YouTubeTool` requiere que `python-vlc` pueda acceder a la librería VLC nativa del sistema operativo.
- `YouTubeTool` requiere que VLC esté instalado como aplicación del sistema (no como paquete Python): en Linux `sudo apt install vlc`, en Windows desde https://videolan.org.
- Usar siempre `pathlib.Path` para rutas de archivo en lugar de strings con `/` hardcodeado para garantizar compatibilidad con Windows.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["4.2"] },
    { "id": 5, "tasks": ["4.3", "4.4", "4.5"] },
    { "id": 6, "tasks": ["4.6", "2.5", "2.6"] },
    { "id": 7, "tasks": ["6"] },
    { "id": 8, "tasks": ["6.1"] },
    { "id": 9, "tasks": ["8"] },
    { "id": 10, "tasks": ["9.1"] },
    { "id": 11, "tasks": ["9.2", "10.1", "11.1", "12.1"] },
    { "id": 12, "tasks": ["9.3", "10.2", "10.3", "11.2", "12.2"] },
    { "id": 13, "tasks": ["13.1"] },
    { "id": 14, "tasks": ["13.2", "13.3"] },
    { "id": 15, "tasks": ["15.1"] },
    { "id": 16, "tasks": ["15.2"] },
    { "id": 17, "tasks": ["17.1", "17.2", "17.3"] }
  ]
}
```
