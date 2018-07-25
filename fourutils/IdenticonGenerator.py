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
                 size=64, saturation=0.7, lightness=0.5, inverted=False):
        self.background = background
        self.margin = margin
        self.size = size
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
        rectangles = []
        baseMargin = floor(self.size * self.margin)
        cell = floor((self.size - (baseMargin * 2)) / 5)
        margin = floor((self.size - cell * 5) / 2)
        background_str = self.get_rgba_string(*self.get_background(hash))
        foreground_str = self.get_rgba_string(*self.get_foreground(hash))

        # the first 15 characters of the hash control the pixels (even/odd)
        # they are drawn down the middle first, then mirrored outwards
        for i in range(15):
            if int(hash[i], 16) % 2:
                # If value is even, skip, this is blank.
                continue
            
            if i < 5:
                rectangles.append(Rect(
                    x=2 * cell + margin,
                    y=i * cell + margin,
                    width=cell,
                    height=cell
                ))
            elif i < 10:
                rectangles.append(Rect(
                    x=1 * cell + margin,
                    y=(i - 5) * cell + margin,
                    width=cell,
                    height=cell
                ))
                rectangles.append(Rect(
                    x=3 * cell + margin,
                    y=(i - 5) * cell + margin,
                    width=cell,
                    height=cell
                ))
            elif i < 15:
                rectangles.append(Rect(
                    x=0 * cell + margin,
                    y=(i - 10) * cell + margin,
                    width=cell,
                    height=cell
                ))
                rectangles.append(Rect(
                    x=4 * cell + margin,
                    y=(i - 10) * cell + margin,
                    width=cell,
                    height=cell
                ))
            
        return rectangles

    def dump(self, hash):
        stroke = self.size * 0.005

        background_str = self.get_rgba_string(*self.get_background(hash))
        foreground_str = self.get_rgba_string(*self.get_foreground(hash))

        xml = (f"<svg xmlns='http://www.w3.org/2000/svg'"
                   f" width='{self.size}' height='{self.size}'"
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
