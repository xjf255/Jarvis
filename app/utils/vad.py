import collections
import queue
import sys
import numpy as np
import sounddevice as sd
import webrtcvad
from app.utils.stt import transcribe_audio

# --- Configuración ---
SAMPLE_RATE = 16000          # webrtcvad soporta 8000, 16000, 32000, 48000
FRAME_DURATION_MS = 30       # duración de cada frame analizado
PADDING_DURATION_MS = 300    # ventana de contexto para decidir inicio/fin de voz
VAD_AGGRESSIVENESS = 2       # 0 (permisivo) a 3 (estricto)

vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
audio_queue = queue.Queue()


class Frame:
    def __init__(self, bytes_data, timestamp, duration):
        self.bytes = bytes_data
        self.timestamp = timestamp
        self.duration = duration


def audio_callback(indata, frames, time_info, status):
    """Se ejecuta automáticamente cada vez que sounddevice tiene nuevo audio."""
    if status:
        print(status, file=sys.stderr)
    # Convierte a PCM 16-bit (formato que espera webrtcvad)
    audio_queue.put(bytes(indata))


def frame_stream_generator():
    """Genera Frames en tiempo real a partir de la cola de audio del micrófono."""
    n = int(SAMPLE_RATE * (FRAME_DURATION_MS / 1000.0) * 2)  # bytes por frame
    buffer = b''
    timestamp = 0.0
    duration = (float(n) / SAMPLE_RATE) / 2.0

    while True:
        buffer += audio_queue.get()
        while len(buffer) >= n:
            frame_bytes = buffer[:n]
            buffer = buffer[n:]
            yield Frame(frame_bytes, timestamp, duration)
            timestamp += duration


def vad_collector(frames):
    """Misma lógica del script original: detecta inicio/fin de voz."""
    num_padding_frames = int(PADDING_DURATION_MS / FRAME_DURATION_MS)
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []

    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, SAMPLE_RATE)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            if num_voiced > 0.9 * int(ring_buffer.maxlen or num_padding_frames):
                triggered = True
                print("🎙️  Detecté que empezaste a hablar...")
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            if num_unvoiced > 0.9 * int(ring_buffer.maxlen or num_padding_frames):
                print("🔇 Silencio detectado, procesando...")
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []


def process_segment(pcm_audio):
    """Aquí es donde conectas Whisper + Claude + XTTS."""
    audio_np = np.frombuffer(pcm_audio, dtype=np.int16).astype(np.float32) / 32768.0
    print(f"Segmento capturado: {len(audio_np) / SAMPLE_RATE:.2f} segundos")
    # TODO: 1. Pasar audio_np a Whisper -> texto
    transcription = transcribe_audio(audio_np)
    print(f"Transcripción: {transcription}")
    # TODO: 2. Pasar texto a la API de Claude -> respuesta
    # TODO: 3. Pasar respuesta a XTTS -> audio de salida
    # TODO: 4. Reproducir con sounddevice


def main():
    print("Escuchando... (Ctrl+C para salir)")
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=int(SAMPLE_RATE * FRAME_DURATION_MS / 1000),
        dtype='int16',
        channels=1,
        callback=audio_callback,
    ):
        frames = frame_stream_generator()
        segments = vad_collector(frames)
        for segment in segments:
            process_segment(segment)
