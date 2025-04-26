import numpy as np
from moviepy import ImageClip
from PIL import Image, ImageDraw

def rounded_mask(size, radius):
    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    mask_array = np.array(mask) / 255.0
    return ImageClip(mask_array, is_mask=True)
