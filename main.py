import os
import sys
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import numpy as np
import sounddevice as sd
import soundfile as sf
from app.utils.llm import LLMClient
from app.utils.tool_dispatcher import ToolDispatcher
from app.utils.stt import transcribe_audio
from app.utils.tts import synthesize_text_to_file
from app.utils.vad import (
    vad_collector,
    frame_stream_generator,
    audio_callback,
    audio_queue,
    SAMPLE_RATE,
    FRAME_DURATION_MS,
)
from app.utils.wake_word import detect_wake_word

WAKE_WORD_THRESHOLD: float = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))


class PipelineState(Enum):
    INACTIVE = "inactivo"
    LISTENING = "escuchando"
    PROCESSING = "procesando"
    RESPONDING = "respondiendo"


def run_pipeline():
    """
    Ejecuta el pipeline principal del asistente de voz.
    Gestiona las transiciones de estado: INACTIVE → LISTENING → PROCESSING → RESPONDING → INACTIVE.
    """
    state = PipelineState.INACTIVE
    transcripcion = ""
    print("🎙️ Sistema iniciado. Esperando la palabra de activación 'Jarvis'... (Ctrl+C para salir)")

    try:
        with sd.RawInputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1280) as stream:
            while True:
                frame, _ = stream.read(1280)

                if state == PipelineState.INACTIVE:
                    scores = detect_wake_word(frame)
                    score = max(scores.values()) if scores else 0.0

                    if score >= WAKE_WORD_THRESHOLD:
                        print(f"🎙️  ¡Palabra de activación detectada! (score={score:.2f}) — Escuchando...")
                        state = PipelineState.LISTENING

                elif state == PipelineState.LISTENING:
                    # Vaciar la cola de audio del módulo VAD antes de capturar
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except Exception:
                            break

                    # Abrir un nuevo stream de audio dedicado al VAD
                    with sd.RawInputStream(
                        samplerate=SAMPLE_RATE,
                        blocksize=int(SAMPLE_RATE * FRAME_DURATION_MS / 1000),
                        dtype='int16',
                        channels=1,
                        callback=audio_callback,
                    ):
                        frames = frame_stream_generator()
                        for pcm_segment in vad_collector(frames):
                            audio_np = (
                                np.frombuffer(pcm_segment, dtype=np.int16)
                                .astype(np.float32) / 32768.0
                            )
                            transcripcion = transcribe_audio(audio_np)
                            break  # Solo procesar el primer segmento

                    if not transcripcion.strip():
                        print("⚠️  No se detectó texto en el audio. Volviendo a esperar...")
                        state = PipelineState.INACTIVE
                    else:
                        print(f"📝 Transcripción: {transcripcion}")
                        state = PipelineState.PROCESSING

                elif state == PipelineState.PROCESSING:
                    try:
                        llm_response = llm_client.generate(transcripcion)

                        if llm_response.type == "text":
                            respuesta = llm_response.text
                        elif llm_response.type == "tool_call":
                            print(f"🔧 Usando herramienta: {llm_response.tool_name}")
                            respuesta = tool_dispatcher.dispatch(
                                llm_response.tool_name, llm_response.tool_args or {}
                            )

                        # print(f"🔧 Respuesta de la herramienta: {respuesta}")
                        print(f"🤖 Jarvis: {respuesta}")
                        synthesize_text_to_file(
                            respuesta,
                            Path("app") / "resources" / "audio.wav",
                            "es",
                            Path("output.wav"),
                            speed=TTS_SPEED,
                        )
                        state = PipelineState.RESPONDING
                    except Exception as e:
                        print(f"[Error recuperable] {type(e).__name__}: {e}")
                        state = PipelineState.INACTIVE

                elif state == PipelineState.RESPONDING:
                    try:
                        data, samplerate = sf.read(Path("output.wav"))
                        sd.play(data, samplerate)
                        sd.wait()
                        print("✅ Respuesta completada. Esperando nueva activación...")
                    except Exception as e:
                        print(f"[Error recuperable] {type(e).__name__}: {e}")
                    finally:
                        state = PipelineState.INACTIVE

    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido. ¡Hasta pronto!")
        sd.stop()


try:
    llm_client = LLMClient()
    tool_dispatcher = ToolDispatcher()
except ValueError as e:
    print(f"[Error de configuración] {e}")
    sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
