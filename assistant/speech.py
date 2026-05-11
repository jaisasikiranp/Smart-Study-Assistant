import io
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

SAMPLE_RATE = 16000

class SpeechProcessor:
    @staticmethod
    def record_audio(max_duration=10, silence_sec=2.0, ambient_threshold=None, energy_threshold=200, save_path=None):
        chunk = int(SAMPLE_RATE * 0.1)          # 100ms chunks
        max_chunks = int(max_duration / 0.1)
        silence_chunks = int(silence_sec / 0.1)

        frames = []
        silent_count = 0
        speech_started = False

        # Use provided threshold or default
        ambient = ambient_threshold if ambient_threshold is not None else energy_threshold

        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=chunk)
        stream.start()
        try:
            for _ in range(max_chunks):
                data, _ = stream.read(chunk)
                energy = np.abs(data).mean()
                frames.append(data.copy())

                if energy > ambient:
                    speech_started = True
                    silent_count = 0
                elif speech_started:
                    silent_count += 1
                    if silent_count >= silence_chunks:
                        break   # stop after silence following speech
        finally:
            stream.stop()
            stream.close()

        if not speech_started:
            return None

        audio_np = np.concatenate(frames, axis=0)
        
        # Save to file if path provided
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            sf.write(save_path, audio_np, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            print(f"[Speech] Audio saved to {save_path}")

        buf = io.BytesIO()
        sf.write(buf, audio_np, SAMPLE_RATE, format='WAV', subtype='PCM_16')
        buf.seek(0)
        with sr.AudioFile(buf) as source:
            return sr.Recognizer().record(source)

    @staticmethod
    def recognize(audio, recognizer, language="en-US"):
        """Wrapper for Google Speech Recognition with confidence capture."""
        try:
            result = recognizer.recognize_google(audio, language=language, show_all=True)
            if not result or 'alternative' not in result:
                return None, 0.0
            
            best_alt = result['alternative'][0]
            return best_alt['transcript'], best_alt.get('confidence', 0.0)
        except Exception:
            return None, 0.0
