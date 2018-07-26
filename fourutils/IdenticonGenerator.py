from dataclasses import dataclass
from math import floor, ceil
from colorsys import hls_to_rgb


@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float


class IdenticonGenerator(object):
    def __init__(self, background=(240, 240, 240, 1.0), margin=0.16,
                 image_size=64, saturation=0.8, lightness=0.5, inverted=False,
                 pixels=5):
        self.background = background
        self.margin = margin
        self.pixels = pixels
        self.image_size = image_size
        self.saturation = saturation
        self.lightness = lightness
        self.inverted = inverted
    
    def get_hash_color(self, hash):
        hue = int(hash[-7:], 16) / 0xfffffff
        return [i*255 for i in hls_to_rgb(hue, self.lightness, self.saturation)]
    
    def get_background(self, hash):
        if self.inverted:
            return self.get_hash_color(hash)
        return self.background
    
    def get_foreground(self, hash):
        if self.inverted:
            return self.background
        return self.get_hash_color(hash)
    
    def get_rectangles(self, hash):
        cols = ceil(self.pixels / 2)

        rectangles = []
        baseMargin = floor(self.image_size * self.margin)
        cell = floor((self.image_size - (baseMargin * 2)) / self.pixels)
        margin = floor((self.image_size - cell * self.pixels) / 2)
        background_str = self.get_rgba_string(*self.get_background(hash))
        foreground_str = self.get_rgba_string(*self.get_foreground(hash))

        for i in range(self.pixels * cols):
            if int(hash[i], 16) % 2:
                # If value is even, skip, this is blank.
                continue
            
            if i < self.pixels and self.pixels % 2:
                # Center column
                rectangles.append(Rect(
                    x=(cols - 1) * cell + margin,
                    y=i * cell + margin,
                    width=cell,
                    height=cell
                ))
            else:
                col = self.pixels * floor(i / self.pixels)
                distance = cols - (col / self.pixels)

                y = (i - col) * cell + margin
                rectangles.append(Rect(
                    x=((distance - 1) * cell) + margin,
                    y=y,
                    width=cell,
                    height=cell
                ))
                rectangles.append(Rect(
                    x=((self.pixels - distance) * cell) + margin,
                    y=y,
                    width=cell,
                    height=cell
                ))
            
        return rectangles

    def dump(self, hash):
        stroke = self.image_size * 0.005

        background_str = self.get_rgba_string(*self.get_background(hash))
        foreground_str = self.get_rgba_string(*self.get_foreground(hash))

        xml = (f"<svg xmlns='http://www.w3.org/2000/svg'"
                   f" width='{self.image_size}' height='{self.image_size}'"
                   f" style='background-color: {background_str}'>"
               f"<g style='fill: {foreground_str}; stroke: {foreground_str}; stroke-width: {stroke};'>")
        for rect in self.get_rectangles(hash):
            xml += (f"<rect x='{rect.x}'"
                         f" y='{rect.y}'"
                         f" width='{rect.width}'"
                         f" height='{rect.height}'/>")
        xml += "</g></svg>"

        return xml
    
    @classmethod
    def get_rgba_string(cls, red, green, blue, alpha=1.0):
        return f"rgba({round(red)}, {round(green)}, {round(blue)}, {alpha})"
