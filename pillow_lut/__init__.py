from __future__ import division, unicode_literals, absolute_import

try:
    from PIL import ImageFilter
except ImportError:
    raise ImportError("Pillow is not installed. "
                      "Please install latest Pillow or Pillow-SIMD package.")

if not hasattr(ImageFilter, "Color3DLUT"):
    raise ImportError("Pillow with the color LUT transformations is required. "
                      "Please install latest Pillow or Pillow-SIMD package.")

from .loaders import load_cube_file