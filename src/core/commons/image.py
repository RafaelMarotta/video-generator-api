from core.commons.masks import rounded_mask
from moviepy.video.VideoClip import VideoClip, ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image
import numpy as np
import tempfile
import os


def add_rounded_border_to_image_clip(
    image_clip: ImageClip,
    border_color=(255, 245, 230),
    border_padding=40,
    border_radius=50,
):
    width, height = image_clip.size
    duration = image_clip.duration
    bg = ColorClip(size=(width + border_padding * 2, height + border_padding * 2), color=border_color)
    mask_array = rounded_mask(bg.size, radius=border_radius)
    bg = bg.with_mask(mask_array)
    bg = bg.with_duration(duration)
    return CompositeVideoClip([bg, image_clip.with_position((border_padding, border_padding))])

