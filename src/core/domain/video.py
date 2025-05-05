import json
from core.domain.pipeline import Step
from core.domain.progress_manager import progress_manager
from moviepy import concatenate_videoclips, AudioFileClip, VideoClip, CompositeAudioClip, concatenate_audioclips
from proglog import ProgressBarLogger
from typing import Callable


class CustomProgressLogger(ProgressBarLogger):
  def __init__(self, video_id: str):
    super().__init__()
    self.video_id = video_id

  def bars_callback(self, bar, attr, value, old_value=None):
    try:
      total = self.bars[bar].get("total", 1)
      percent = round((value / total) * 100, 2)

      progress_manager.publish(self.video_id, json.dumps({
        "event": "export_progress",
        "video_id": self.video_id,
        "step": bar,
        "progress": percent
      }))
    except Exception as e:
      print("Logger error:", e)

  def close(self):
    print("finished")



class ConcatenateVideoStep(Step):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
    super().__init__(name, description, input_transformer)

  def execute(self, input: dict, context: dict):
    video_clips: list[VideoClip] = context["composites"]
    final_clip = concatenate_videoclips(video_clips, method="compose")
    context[self.name] = {"final_video": final_clip}


class ExportVideo(Step):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
    super().__init__(name, description, input_transformer)

  def execute(self, input: dict, context: dict):
    final_video = input["final_video"]
    output_path = input.get("output_path", "output.mp4")
    video_id = context.get("id")

    logger = CustomProgressLogger(video_id)
    final_video.write_videofile(output_path, fps=10, logger=logger)
    progress_manager.publish(self.video_id, json.dumps({
      "event": "video_ready",
      "video_id": self.video_id
    }))


class AddBackgroundMusicStep(Step):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
    super().__init__(name, description, input_transformer)

  def execute(self, input: dict, context: dict):
    final_video = input["final_video"]
    background_music_path = input["background_music_path"]

    music_clip = AudioFileClip(background_music_path)
    n_loops = int(final_video.duration // music_clip.duration) + 1
    repeated_music = concatenate_audioclips([music_clip] * n_loops)
    repeated_music = repeated_music.with_duration(final_video.duration)

    if final_video.audio:
      final_audio = CompositeAudioClip([final_video.audio, repeated_music.with_volume_scaled(0.2)])
    else:
      final_audio = repeated_music

    final_video = final_video.with_audio(final_audio)
    context[self.name] = {"final_video": final_video}