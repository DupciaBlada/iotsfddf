import whisper
import pyaudio
import wave
import os
import paho.mqtt.client as mqtt
import ssl  # Dodano moduł SSL

os.environ["PATH"] += os.pathsep + r"C:\Users\victo\Desktop\ffmpeg\ffmpeg\bin"

MQTT_BROKER = "h7349222.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
MQTT_TOPIC = "emqx/speech-to-text"
MQTT_USERNAME = "chatadoriana"
MQTT_PASSWORD = "chatadoriana"
CERT_FILE = "emqxsl-ca.crt"  # Plik certyfikatu

model = whisper.load_model("base")

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

def record_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording Finished.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def publish_message(message):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Konfiguracja TLS z certyfikatem
        client.tls_set(
            ca_certs=CERT_FILE,  # Ścieżka do pliku certyfikatu
            certfile=None,       # Certyfikat klienta (jeśli wymagany, na razie None)
            keyfile=None,        # Klucz prywatny klienta (jeśli wymagany, na razie None)
            tls_version=ssl.PROTOCOL_TLS,  # Wersja TLS
            ciphers=None         # Domyślne szyfrowanie
        )
        client.tls_insecure_set(False)  # Weryfikuj certyfikat serwera
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Publikowanie wiadomości
        result = client.publish(MQTT_TOPIC, message)
        print(f"Published to {MQTT_TOPIC}: {message}, result: {result}")
        if result[0] != mqtt.MQTT_ERR_SUCCESS:
            print("Error: Publishing failed.")
        client.disconnect()
    except Exception as e:
        print(f"Error publishing message: {e}")

def main():
    while True:
        record_audio()

        print("Processing audio...")
        result = model.transcribe(WAVE_OUTPUT_FILENAME, language="pl")
        os.remove(WAVE_OUTPUT_FILENAME)

        transcription = result["text"]
        print(f"Transcription: {transcription}")

        publish_message(transcription)

if __name__ == "__main__":
    main()
