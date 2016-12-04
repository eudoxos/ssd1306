#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Richard Hull
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
from oled.device import device
import oled.mixin as mixin


class emulator(mixin.noop, mixin.capabilities, device):
    """
    Base class for emulated OLED driver classes
    """
    def __init__(self, width, height, transform="scale2x", scale=2):
        import pygame
        self._pygame = pygame
        self.capabilities(width, height, mode="RGB")
        self._scale = 1 if transform == "none" else scale
        self._transform = getattr(transformer(pygame, width, height, scale),
                                  "none" if scale == 1 else transform)

    def to_surface(self, im):
        im = im.convert("RGB")
        mode = im.mode
        size = im.size
        data = im.tobytes()
        del im

        surface = self._pygame.image.fromstring(data, size, mode)
        return self._transform(surface)


class capture(emulator):
    """
    Pseudo-device that acts like an OLED display, except that it writes
    the image to a numbered PNG file when the :func:`display` method
    is called.

    While the capability of an OLED device is monochrome, there is no
    limitation here, and hence supports 24-bit color depth.
    """
    def __init__(self, width=128, height=64, file_template="oled_{0:06}.png", transform="scale2x", scale=2, **kwargs):
        super(capture, self).__init__(width, height, transform, scale)
        self._count = 0
        self._file_template = file_template

    def display(self, image):
        """
        Takes an image and dumps it to a numbered PNG file.
        """
        assert(image.size[0] == self.width)
        assert(image.size[1] == self.height)

        self._count += 1
        filename = self._file_template.format(self._count)
        surface = self.to_surface(image)
        print("Writing: {0}".format(filename))
        self._pygame.image.save(surface, filename)


class pygame(emulator):
    """
    Pseudo-device that acts like an OLED display, except that it renders
    to an displayed window. The frame rate is limited to 60FPS (much faster
    than a Raspberry Pi can acheive, but this can be overridden as necessary).

    While the capability of an OLED device is monochrome, there is no
    limitation here, and hence supports 24-bit color depth.

    :mod:`pygame` is used to render the emulated display window, and it's
    event loop is checked to see if the ESC key was pressed or the window
    was dismissed: if so `sys.exit()` is called.
    """
    def __init__(self, width=128, height=64, frame_rate=60, transform="scale2x", scale=2, **kwargs):
        super(pygame, self).__init__(width, height, transform, scale)
        self._pygame.init()
        self._pygame.font.init()
        self._pygame.display.set_caption("OLED Emulator")
        self._clock = self._pygame.time.Clock()
        self._fps = frame_rate
        self._screen = self._pygame.display.set_mode((width * self._scale, height * self._scale))
        self._screen.fill((0, 0, 0))
        self._pygame.display.flip()

    def _abort(self):
        keystate = self._pygame.key.get_pressed()
        return keystate[self._pygame.K_ESCAPE] or self._pygame.event.peek(self._pygame.QUIT)

    def display(self, image):
        """
        Takes an image and renders it to a pygame display surface.
        """
        assert(image.size[0] == self.width)
        assert(image.size[1] == self.height)

        self._clock.tick(self._fps)
        self._pygame.event.pump()

        if self._abort():
            self._pygame.quit()
            sys.exit()

        surface = self.to_surface(image)
        self._screen.blit(surface, (0, 0))
        self._pygame.display.flip()


class transformer(object):
    """
    Helper class used to dispatch transformation operations.
    """
    def __init__(self, pygame, width, height, scale):
        self._pygame = pygame
        self._output_size = (width * scale, height * scale)
        self._scale = scale

    def none(self, surface):
        """
        No-op transform - used when scale = 1
        """
        return surface

    def scale2x(self, surface):
        """
        Scales using the AdvanceMAME Scale2X algorithm which does a
        'jaggie-less' scale of bitmap graphics.
        """
        assert(self._scale == 2)
        return self._pygame.transform.scale2x(surface)

    def smoothscale(self, surface):
        """
        Smooth scaling using MMX or SSE extensions if available
        """
        return self._pygame.transform.smoothscale(surface, self._output_size)

    def scale(self, surface):
        """
        Fast scale operation that does not sample the results
        """
        return self._pygame.transform.scale(surface, self._output_size)