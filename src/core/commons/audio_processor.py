import numpy as np
from moviepy.audio.AudioClip import AudioArrayClip
from google.cloud import texttospeech

def generate_tts(text, language="pt-br", voice_name=None, speaking_rate=1.0, ssml=True):
    client = texttospeech.TextToSpeechClient()

    # Set default voice and language based on language parameter
    if language == "pt-br":
        language_code = "pt-BR"
        if not voice_name:
            voice_name = "pt-BR-Wavenet-B"
    else:
        language_code = "en-US"
        if not voice_name:
            voice_name = "en-US-Wavenet-D"

    # Configure the voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

    # Configure the audio format and speaking rate
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate
    )

    # Prepare the synthesis input, either plain text or SSML
    if ssml:
        # Wrap the input in <speak> tags for SSML
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)

    # Perform the text-to-speech request
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content

def create_silence(duration, fps=44100):
    n_samples = int(duration * fps)
    silence = np.zeros((n_samples, 1))
    return AudioArrayClip(silence, fps=fps)
