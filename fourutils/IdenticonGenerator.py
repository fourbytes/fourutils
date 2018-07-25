from math import floor, ceil
from colorsys import hls_to_rgb


class IdenticonGenerator(object):
    def __init__(self, background=(240, 240, 240, 1.0), margin=0.16,
                 size=64, saturation=0.7, lightness=0.5, format='svg',
                 inverted=False):
        self.background = background
        self.margin = margin
        self.size = size
        self.saturation = saturation
        self.lightness = lightness
        self.format = format
        self.inverted = inverted
    
    def calculate_foreground(self, hash):
        hue = int(hash[-7:], 16) / 0xfffffff
        return [i*255 for i in hls_to_rgb(hue, self.lightness, self.saturation)]
    
    def get_background(self, hash):
        if self.inverted:
            return self.calculate_foreground(hash)
        return self.background
    
    def get_foreground(self, hash):
        if self.inverted:
            return self.background
        return self.calculate_foreground(hash)
    
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
                color = background_str
            else:
                color = foreground_str
            
            if i < 5:
                rectangles.append({
                    'x': 2 * cell + margin,
                    'y': i * cell + margin,
                    'w': cell,
                    'h': cell,
                    'color': color
                })
            elif i < 10:
                rectangles.append({
                    'x': 1 * cell + margin,
                    'y': (i - 5) * cell + margin,
                    'w': cell,
                    'h': cell,
                    'color': color
                })
                rectangles.append({
                    'x': 3 * cell + margin,
                    'y': (i - 5) * cell + margin,
                    'w': cell,
                    'h': cell,
                    'color': color
                })
            elif i < 15:
                rectangles.append({
                    'x': 0 * cell + margin,
                    'y': (i - 10) * cell + margin,
                    'w': cell,
                    'h': cell,
                    'color': color
                })
                rectangles.append({
                    'x': 4 * cell + margin,
                    'y': (i - 10) * cell + margin,
                    'w': cell,
                    'h': cell,
                    'color': color
                })
            
        return rectangles

    def dump(self, hash):
        stroke = self.size * 0.005

        background_str = self.get_rgba_string(*self.get_background(hash))
        foreground_str = self.get_rgba_string(*self.get_foreground(hash))

        xml = f"""
        <svg xmlns='http://www.w3.org/2000/svg'
             width='{self.size}' height='{self.size}'
             style='background-color: {background_str}'>
            <g style='fill: {foreground_str}; stroke: {foreground_str}; stroke-width: {stroke};'>"""
        for rect in self.get_rectangles(hash):
            if rect['color'] == background_str: continue
            xml += f"""
<rect x='{rect['x']}'
      y='{rect['y']}'
      width='{rect['w']}'
      height='{rect['h']}'/>"""
        xml += "</g></svg>"

        return xml
    
    @classmethod
    def get_rgba_string(cls, red, green, blue, alpha=1.0):
        return f"rgba({round(red)}, {round(green)}, {round(blue)}, {alpha})"
