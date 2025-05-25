import pyaudio
import wave
import whisper
import keyboard

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAV_OUTPUT = "output.wav"

model = whisper.load_model("base")

def record_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording... (hold SPACEBAR)")
    frames = []

    while keyboard.is_pressed("space"):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(WAV_OUTPUT, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def transcribe():
    result = model.transcribe(WAV_OUTPUT)
    print("Transcription:")
    print(result["text"])

# MAIN
print("Hold SPACEBAR to record:")
keyboard.wait("space")
record_audio()
transcribe()
                                                                         