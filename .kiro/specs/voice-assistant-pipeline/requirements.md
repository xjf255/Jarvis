# Requirements Document

## Introduction

Este documento describe los requisitos funcionales para completar el pipeline del asistente de voz Jarvis. El proyecto ya cuenta con módulos parcialmente implementados (VAD, STT, TTS y detección de wake word). El objetivo es conectar todos los componentes en un pipeline cohesivo de extremo a extremo:

**wake word → escuchar (VAD) → STT → LLM → TTS → reproducir → estado inactivo**

El módulo LLM se integrará usando OpenRouter (API compatible con OpenAI) en lugar de la API de Anthropic, aprovechando modelos gratuitos como `meta-llama/llama-3.1-8b-instruct:free`. La configuración del sistema se gestionará mediante variables de entorno cargadas con `python-dotenv`.

Además del flujo conversacional básico, el sistema incorpora un **Sistema de Herramientas (Tool Use)**: el LLM puede decidir ejecutar acciones concretas (reproducir música en YouTube, enviar mensajes por WhatsApp, abrir el navegador) en lugar de generar únicamente texto de respuesta. El `Pipeline_Controller` coordina la ejecución de estas herramientas a través del `ToolDispatcher`.

**Plataformas soportadas:** Linux y Windows. El sistema no soporta Android ni otros sistemas operativos móviles.

---

## Glossary

- **Pipeline**: Flujo de procesamiento completo desde la detección de voz hasta la respuesta sintetizada.
- **VAD** (Voice Activity Detection): Módulo que detecta actividad de voz en tiempo real y emite segmentos PCM.
- **STT** (Speech-to-Text): Módulo que transcribe audio PCM a texto usando OpenAI Whisper.
- **LLM** (Large Language Model): Modelo de lenguaje que genera respuestas en texto a partir de una consulta. En este sistema se accede a través de OpenRouter.
- **TTS** (Text-to-Speech): Módulo que sintetiza texto en audio usando Coqui XTTS v2 con clonación de voz.
- **Wake_Word_Detector**: Módulo que detecta la palabra de activación "Jarvis" usando openwakeword.
- **LLMClient**: Clase Python ubicada en `app/utils/llm.py` que encapsula la comunicación con OpenRouter. Soporta tanto respuestas de texto como tool calls mediante function calling.
- **Pipeline_Controller**: Componente principal en `main.py` que orquesta todos los módulos en el pipeline completo, incluyendo la ejecución de herramientas a través del `ToolDispatcher`.
- **OpenRouter**: Servicio de proxy de APIs de LLM que expone una interfaz compatible con OpenAI, accesible en `https://openrouter.ai/api/v1`.
- **PCM**: Datos de audio en formato Pulse-Code Modulation de 16 bits, emitidos por el VAD.
- **Estado_Inactivo**: Estado del sistema donde el Pipeline_Controller espera la palabra de activación.
- **Estado_Escuchando**: Estado del sistema donde el VAD captura la consulta del usuario.
- **Estado_Procesando**: Estado del sistema donde STT, LLM y TTS (o herramientas) procesan la consulta.
- **Estado_Respondiendo**: Estado del sistema donde el audio de respuesta se reproduce al usuario.
- **ToolDispatcher**: Clase Python ubicada en `app/utils/tool_dispatcher.py` que recibe un `tool_call` del `LLMClient`, identifica la herramienta a ejecutar, extrae los parámetros y retorna un string de resultado para que el TTS lo lea.
- **tool_call**: Objeto estructurado retornado por el `LLMClient` cuando el LLM decide ejecutar una herramienta en lugar de responder con texto. Contiene el nombre de la herramienta y sus parámetros en formato JSON.
- **Function Calling**: Mecanismo de la API compatible con OpenAI que permite al LLM retornar llamadas a funciones estructuradas en lugar de texto libre, usando el campo `tool_calls` en la respuesta.
- **YouTubeTool**: Módulo `app/tools/youtube.py` que gestiona búsqueda y reproducción de audio/video de YouTube.
- **WhatsAppTool**: Módulo `app/tools/whatsapp.py` que gestiona lectura y envío de mensajes en WhatsApp Web.
- **BrowserTool**: Módulo `app/tools/browser.py` que gestiona búsquedas web y apertura de URLs en el navegador del sistema.
- **yt-dlp**: Herramienta de línea de comandos y librería Python para extraer streams de audio/video de YouTube.
- **python-vlc**: Binding Python para la librería VLC, usado para reproducción de streams de audio.

---

## Requirements

### Requisito 1: Módulo LLM con OpenRouter

**Historia de usuario:** Como desarrollador, quiero un módulo LLM encapsulado que se comunique con OpenRouter, para que el pipeline pueda generar respuestas de texto a partir de las transcripciones del usuario.

#### Criterios de Aceptación

1. THE LLMClient SHALL inicializarse leyendo `OPENROUTER_API_KEY` desde las variables de entorno.
2. THE LLMClient SHALL usar `LLM_MODEL` como identificador de modelo, con valor por defecto `meta-llama/llama-3.1-8b-instruct:free` si la variable no está definida.
3. THE LLMClient SHALL configurar el cliente `openai` de Python apuntando a la base URL `https://openrouter.ai/api/v1`.
4. WHEN LLMClient recibe un texto de consulta del usuario, THE LLMClient SHALL enviar una solicitud de completado de chat a OpenRouter incluyendo un mensaje de sistema y el mensaje del usuario.
5. THE LLMClient SHALL incluir un mensaje de sistema que instruya al modelo a responder de forma concisa en español, con respuestas adecuadas para síntesis de voz (sin markdown, sin listas, sin caracteres especiales).
6. THE LLMClient SHALL limitar la respuesta del modelo a un máximo de 300 tokens (`max_tokens=300`).
7. WHEN la API de OpenRouter devuelve una respuesta exitosa, THE LLMClient SHALL retornar únicamente el texto del primer mensaje de la respuesta.
8. IF `OPENROUTER_API_KEY` no está definida al inicializar LLMClient, THEN THE LLMClient SHALL lanzar una excepción `ValueError` con un mensaje descriptivo.
9. IF la llamada a la API de OpenRouter falla, THEN THE LLMClient SHALL propagar la excepción para que el Pipeline_Controller la pueda manejar.

---

### Requisito 2: Gestión de configuración con variables de entorno

**Historia de usuario:** Como operador del sistema, quiero que toda la configuración se cargue desde un archivo `.env`, para que el sistema sea configurable sin modificar código fuente.

#### Criterios de Aceptación

1. THE Pipeline_Controller SHALL cargar las variables de entorno desde el archivo `.env` usando `python-dotenv` al inicio de la ejecución.
2. THE Pipeline_Controller SHALL leer `OPENROUTER_API_KEY` como variable requerida para la inicialización del LLMClient.
3. THE Pipeline_Controller SHALL leer `LLM_MODEL` con valor por defecto `meta-llama/llama-3.1-8b-instruct:free`.
4. THE Pipeline_Controller SHALL leer `WAKE_WORD_THRESHOLD` con valor por defecto `0.5`, interpretado como número flotante.
5. THE Pipeline_Controller SHALL leer `TTS_SPEED` con valor por defecto `1.0`, interpretado como número flotante.
6. IF `OPENROUTER_API_KEY` está ausente o vacía en el archivo `.env`, THEN THE Pipeline_Controller SHALL mostrar un mensaje de error descriptivo y terminar la ejecución.

---

### Requisito 3: Detección de wake word integrada al pipeline

**Historia de usuario:** Como usuario, quiero que el asistente solo se active cuando digo "Jarvis", para que no procese audio de fondo de forma continua.

#### Criterios de Aceptación

1. WHILE el sistema está en Estado_Inactivo, THE Wake_Word_Detector SHALL analizar frames de audio del micrófono de forma continua.
2. WHEN el Wake_Word_Detector detecta "Jarvis" con una puntuación mayor o igual al valor de `WAKE_WORD_THRESHOLD`, THE Pipeline_Controller SHALL transicionar al Estado_Escuchando.
3. WHEN el sistema transiciona al Estado_Escuchando, THE Pipeline_Controller SHALL imprimir un mensaje de confirmación indicando que la palabra de activación fue detectada.
4. THE Wake_Word_Detector SHALL procesar frames de audio de 1280 muestras a 16000 Hz (80ms por frame), conforme al formato requerido por openwakeword.
5. WHILE el sistema está en Estado_Escuchando, Estado_Procesando o Estado_Respondiendo, THE Wake_Word_Detector SHALL suspender el análisis de wake word para evitar activaciones falsas.

---

### Requisito 4: Pipeline de procesamiento de voz de extremo a extremo

**Historia de usuario:** Como usuario, quiero hablar con el asistente y recibir una respuesta de voz, para que la interacción sea completamente oral sin necesidad de teclado.

#### Criterios de Aceptación

1. WHEN el sistema entra en Estado_Escuchando, THE VAD SHALL capturar audio del micrófono y detectar el inicio y fin de la locución del usuario.
2. WHEN el VAD detecta fin de voz (silencio sostenido), THE Pipeline_Controller SHALL transicionar al Estado_Procesando con el segmento PCM capturado.
3. WHEN el sistema entra en Estado_Procesando, THE STT SHALL transcribir el segmento PCM a texto usando el modelo Whisper configurado.
4. WHEN el STT produce una transcripción, THE LLMClient SHALL generar una respuesta en texto enviando la transcripción a OpenRouter.
5. WHEN el LLMClient produce una respuesta en texto, THE TTS SHALL sintetizar el texto en audio usando XTTS v2 con el archivo de referencia `app/resources/audio.wav` y el idioma `es`.
6. WHEN el TTS produce el audio sintetizado, THE Pipeline_Controller SHALL transicionar al Estado_Respondiendo y reproducir el audio usando `sounddevice`.
7. WHEN la reproducción de audio finaliza, THE Pipeline_Controller SHALL transicionar de vuelta al Estado_Inactivo.
8. THE Pipeline_Controller SHALL usar el valor de `TTS_SPEED` al llamar a la función de síntesis de TTS.
9. IF el STT produce una transcripción vacía o compuesta únicamente de espacios en blanco, THEN THE Pipeline_Controller SHALL descartar el segmento y volver al Estado_Inactivo sin llamar al LLM ni al TTS.

---

### Requisito 5: Manejo de errores y resiliencia del pipeline

**Historia de usuario:** Como operador del sistema, quiero que el asistente se recupere automáticamente de errores transitorios, para que una falla puntual no detenga la sesión completa.

#### Criterios de Aceptación

1. IF la llamada al LLMClient falla por un error de red o de la API, THEN THE Pipeline_Controller SHALL imprimir un mensaje de error descriptivo y volver al Estado_Inactivo sin terminar el proceso.
2. IF la síntesis TTS falla, THEN THE Pipeline_Controller SHALL imprimir un mensaje de error descriptivo y volver al Estado_Inactivo sin terminar el proceso.
3. IF la reproducción de audio falla, THEN THE Pipeline_Controller SHALL imprimir un mensaje de error descriptivo y volver al Estado_Inactivo sin terminar el proceso.
4. THE Pipeline_Controller SHALL capturar excepciones `KeyboardInterrupt` y terminar la ejecución de forma limpia, liberando los recursos de audio.
5. WHEN el Pipeline_Controller maneja un error recuperable, THE Pipeline_Controller SHALL imprimir el tipo de excepción y el mensaje asociado para facilitar el diagnóstico.

---

### Requisito 6: Retroalimentación de estado al usuario

**Historia de usuario:** Como usuario, quiero ver mensajes en consola que indiquen el estado del sistema en cada etapa, para saber cuándo hablar y cuándo esperar la respuesta.

#### Criterios de Aceptación

1. WHEN el sistema inicia, THE Pipeline_Controller SHALL imprimir un mensaje indicando que el sistema está listo y esperando la palabra de activación.
2. WHEN el Wake_Word_Detector detecta la palabra de activación, THE Pipeline_Controller SHALL imprimir un mensaje indicando que el wake word fue detectado y el sistema está escuchando.
3. WHEN el VAD detecta fin de voz y comienza el procesamiento, THE Pipeline_Controller SHALL imprimir la transcripción obtenida por el STT.
4. WHEN el LLMClient retorna una respuesta, THE Pipeline_Controller SHALL imprimir el texto de la respuesta generada.
5. WHEN el sistema finaliza la reproducción y vuelve al Estado_Inactivo, THE Pipeline_Controller SHALL imprimir un mensaje indicando que está listo para una nueva activación.

---

### Requisito 7: Sistema de Herramientas (Tool Use)

**Historia de usuario:** Como usuario, quiero que el asistente pueda ejecutar acciones concretas como reproducir música, enviar mensajes de WhatsApp o buscar en internet cuando se lo pida, para que no se limite únicamente a responder con texto.

#### Criterios de Aceptación

1. WHEN el LLMClient envía una solicitud a OpenRouter, THE LLMClient SHALL incluir las definiciones de herramientas disponibles en el formato de function calling compatible con OpenAI.
2. WHEN la respuesta de OpenRouter contiene un `tool_call` en lugar de texto, THE LLMClient SHALL retornar un objeto `LLMResponse` con `type="tool_call"`, el nombre de la herramienta y sus parámetros en formato de diccionario.
3. WHEN la respuesta de OpenRouter contiene texto normal, THE LLMClient SHALL retornar un objeto `LLMResponse` con `type="text"` y el texto de respuesta, manteniendo compatibilidad con el flujo existente.
4. WHEN el Pipeline_Controller recibe un `LLMResponse` con `type="tool_call"`, THE Pipeline_Controller SHALL invocar al ToolDispatcher con el nombre de herramienta y los parámetros extraídos.
5. WHEN el ToolDispatcher ejecuta una herramienta exitosamente, THE ToolDispatcher SHALL retornar un string de confirmación para que el TTS lo lea en voz alta.
6. IF la ejecución de una herramienta falla, THEN THE ToolDispatcher SHALL retornar un string describiendo el error para que el TTS lo lea en voz alta.
7. IF el ToolDispatcher recibe el nombre de una herramienta desconocida, THEN THE ToolDispatcher SHALL retornar un mensaje indicando que la herramienta no está disponible.

---

### Requisito 7.1: Herramienta YouTube

**Historia de usuario:** Como usuario, quiero pedirle al asistente que reproduzca música o videos de YouTube con comandos de voz, para poder escuchar música sin usar el teclado.

#### Criterios de Aceptación

1. WHEN el YouTubeTool recibe `action="play_audio"` y un parámetro `query`, THE YouTubeTool SHALL buscar el término en YouTube, extraer el stream de audio con `yt-dlp` y reproducirlo con `python-vlc` o `mpv`.
2. WHEN el YouTubeTool recibe `action="play_video"` y un parámetro `query`, THE YouTubeTool SHALL buscar el término en YouTube y abrir el video en el navegador del sistema.
3. WHEN el YouTubeTool recibe `action="pause"`, THE YouTubeTool SHALL pausar la reproducción de audio activa si existe alguna.
4. WHEN el YouTubeTool recibe `action="resume"`, THE YouTubeTool SHALL reanudar la reproducción de audio pausada si existe alguna.
5. WHEN el YouTubeTool recibe `action="stop"`, THE YouTubeTool SHALL detener y liberar la reproducción de audio activa si existe alguna.
6. WHEN el YouTubeTool completa una acción exitosamente, THE YouTubeTool SHALL retornar un string de confirmación que incluya el título del contenido reproducido o el estado actual.
7. IF el YouTubeTool no encuentra resultados para un `query`, THEN THE YouTubeTool SHALL retornar un mensaje indicando que no se encontraron resultados.
8. IF el YouTubeTool falla al extraer o reproducir el stream, THEN THE YouTubeTool SHALL retornar un mensaje de error descriptivo.

---

### Requisito 7.2: Herramienta WhatsApp

**Historia de usuario:** Como usuario, quiero pedirle al asistente que lea mis mensajes de WhatsApp o envíe un mensaje a un contacto con comandos de voz, para gestionar mis comunicaciones manos libres.

#### Criterios de Aceptación

1. WHEN el WhatsAppTool recibe `action="read_unread"`, THE WhatsAppTool SHALL acceder a WhatsApp Web y retornar un resumen de los mensajes no leídos.
2. WHEN el WhatsAppTool recibe `action="send_message"`, un parámetro `contact` y un parámetro `message`, THE WhatsAppTool SHALL enviar el mensaje al contacto especificado a través de WhatsApp Web.
3. WHEN el WhatsAppTool completa una acción exitosamente, THE WhatsAppTool SHALL retornar un string de confirmación indicando la acción realizada.
4. IF el WhatsAppTool no encuentra el contacto especificado, THEN THE WhatsAppTool SHALL retornar un mensaje indicando que el contacto no fue encontrado.
5. IF el WhatsAppTool falla al acceder a WhatsApp Web, THEN THE WhatsAppTool SHALL retornar un mensaje de error descriptivo indicando que no fue posible conectarse.

---

### Requisito 7.3: Herramienta Navegador Web

**Historia de usuario:** Como usuario, quiero pedirle al asistente que busque en internet o abra una URL con comandos de voz, para acceder a información o sitios web sin usar el teclado.

#### Criterios de Aceptación

1. WHEN el BrowserTool recibe `action="search"` y un parámetro `query`, THE BrowserTool SHALL abrir el navegador por defecto del sistema con una búsqueda en Google usando el término proporcionado.
2. WHEN el BrowserTool recibe `action="open_url"` y un parámetro `url`, THE BrowserTool SHALL abrir la URL especificada en el navegador por defecto del sistema.
3. WHEN el BrowserTool completa una acción exitosamente, THE BrowserTool SHALL retornar un string de confirmación indicando la acción realizada.
4. IF la URL proporcionada al BrowserTool no tiene un esquema válido (`http://` o `https://`), THEN THE BrowserTool SHALL intentar añadir `https://` como prefijo antes de abrir.
5. IF el BrowserTool falla al abrir el navegador, THEN THE BrowserTool SHALL retornar un mensaje de error descriptivo.

---

### Requisito 8: Compatibilidad multiplataforma Linux y Windows

**Historia de usuario:** Como usuario, quiero poder ejecutar el asistente tanto en Linux como en Windows sin modificar el código fuente, para que sea portable entre mis equipos.

#### Criterios de Aceptación

1. THE sistema SHALL ejecutarse correctamente en Linux (Ubuntu 22.04+) y Windows (Windows 10+) usando Python 3.10+.
2. THE código fuente SHALL usar únicamente APIs de Python que sean compatibles con ambos sistemas operativos; en particular, no SHALL hardcodear rutas absolutas con separadores de sistema (`/` o `\`), usando siempre `pathlib.Path` o `os.path.join`.
3. THE archivo `requirements.txt` SHALL incluir únicamente paquetes disponibles para ambas plataformas en sus versiones especificadas.
4. WHEN el sistema detecta que `python-vlc` no puede acceder a la librería VLC nativa del sistema operativo, THE YouTubeTool SHALL imprimir un mensaje de error descriptivo indicando que VLC debe estar instalado, y retornar un string de error sin lanzar una excepción no controlada.
5. THE archivo `README.md` o `workflow.md` SHALL documentar los pasos de instalación específicos para cada plataforma, incluyendo la instalación de VLC como dependencia del sistema en Windows y Linux.
6. THE sistema NO soporta Android, iOS ni ningún otro sistema operativo móvil o embebido. Esta limitación es intencional y no debe abordarse en esta versión.
