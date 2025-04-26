from core.domain.pipeline import Step
from moviepy import concatenate_videoclips
from typing import Callable

class ConcatenateVideoStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        video_clips: list[VideoClip] = input["video_clips"]
        final_clip = concatenate_videoclips(video_clips, method="compose")
        context[self.name] = {"final_video": final_clip}

class ExportVideo(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        final_video = input["final_video"]
        output_path = input.get("output_path", "output.mp4")
        final_video.write_videofile(output_path, fps=10, logger="bar")

