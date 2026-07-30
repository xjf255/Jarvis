# Proyecto: Asistente de Voz Jarvis

## Descripción

Bot de voz conversacional en Python que responde al nombre "Jarvis". El pipeline completo es:

```
Estado_Inactivo → [wake word "Jarvis"] → Estado_Escuchando → [VAD captura voz]
→ STT (Whisper) → LLM (OpenRouter) → TTS (XTTS v2) → Reproducción → Estado_Inactivo
```

## Stack tecnológico

| Componente | Librería / Servicio |
|---|---|
| Wake word | `openwakeword` + modelo custom `jarvis_model.zip` |
| VAD | `webrtcvad` + `sounddevice` |
| STT | `openai-whisper` (modelo `base`) |
| LLM | OpenRouter API (compatible con `openai` SDK) — modelos gratuitos con sufijo `:free` |
| TTS | Coqui `XTTS v2` (`tts_models/multilingual/multi-dataset/xtts_v2`) |
| Audio I/O | `sounddevice`, `soundfile` |
| Config | `python-dotenv` + archivo `.env` |

## Estructura del proyecto

```
bot_exercise/
├── app/
│   ├── resources/
│   │   ├── audio.wav          # Referencia de voz para clonación TTS
│   │   └── jarvis_model.zip   # Modelo custom de wake word
│   └── utils/
│       ├── vad.py             # VAD — detección de actividad de voz
│       ├── stt.py             # STT — transcripción con Whisper
│       ├── tts.py             # TTS — síntesis con XTTS v2
│       ├── wake_word.py       # Wake word — detección de "Jarvis"
│       └── llm.py             # LLM — cliente OpenRouter (a implementar)
├── main.py                    # Orquestador del pipeline
├── .env                       # Variables de entorno (no commitear)
├── .gitignore
└── requirements.txt
```

## Variables de entorno

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Sí | — | Clave de API de OpenRouter |
| `LLM_MODEL` | No | `meta-llama/llama-3.1-8b-instruct:free` | Modelo a usar en OpenRouter |
| `WAKE_WORD_THRESHOLD` | No | `0.5` | Umbral de confianza para activación |
| `TTS_SPEED` | No | `1.0` | Velocidad de síntesis de voz |

## Parámetros de audio fijos

- Sample rate: **16000 Hz**
- Formato PCM: **int16**, mono, 1 canal
- Frame VAD: **30ms** (480 muestras)
- Frame wake word: **1280 muestras** (80ms) — requerido por openwakeword
- Padding VAD: **300ms**
- VAD aggressiveness: **2**

## Archivo de salida TTS

- Ruta: `output.wav` en la raíz del proyecto
- Se sobreescribe en cada ciclo (comportamiento intencional)
