import sounddevice as sd
import soundfile as sf
from app.utils.tts import synthesize_text_to_file
from app.utils.vad import main as vad_main

# synthesize_text_to_file(
#     text="Bienvenido de regreso, trabajando en un proyecto secreto señor.",
#     speaker_wav="./app/resources/audio.wav",
#     language="es",
#     file_path="output.wav",
#     speed=1.0
# )

# data, samplerate = sf.read("output.wav")
# sd.play(data, samplerate)
# sd.wait()
vad_main()
