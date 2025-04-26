import os
from PIL import ImageFont
import matplotlib.font_manager as fm

def get_valid_font_path(requested_font_path: str) -> str:
    if requested_font_path and os.path.exists(requested_font_path):
        return requested_font_path
    try:
        defaultFontPath = fm.findfont(fm.FontProperties())
        print(f"Font {requested_font_path} not found, using the default font {defaultFontPath}")
        return defaultFontPath
    except Exception:
        defaultFontPath = ImageFont.load_default().path
        print(f"Font {requested_font_path} not found, using the default font {defaultFontPath}")
        return defaultFontPath
