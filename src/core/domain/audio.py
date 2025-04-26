import tempfile
from core.domain.pipeline import Step
from core.commons.audio_processor import generate_tts
from moviepy.audio.io.AudioFileClip import AudioFileClip

class GenerateSpeechStep(Step):
    def __init__(self, name, description, input_transformer=None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        audio_content = generate_tts(input["text_ssml"])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_content)
            audio_path = f.name

        audio_clip = AudioFileClip(audio_path)

        context[self.name] = {
            "audio_clip": audio_clip,
            "audio_path": audio_path,  
        }
