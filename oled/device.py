#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# Example usage:
#
#   from oled.serial import i2c, spi
#   from oled.device import ssd1306, sh1106
#   from oled.render import canvas
#   from PIL import ImageDraw
#
#   serial = i2c(port=1, address=0x3C)
#   device = ssd1306(serial)
#
#   with canvas(device) as draw:
#      draw.rectangle(device.bounding_box, outline="white", fill="black")
#      draw.text(30, 40, "Hello World", fill="white")
#
# As soon as the with-block scope level is complete, the graphics primitives
# will be flushed to the device.
#
# Creating a new canvas is effectively 'carte blanche': If you want to retain
# an existing canvas, then make a reference like:
#
#    c = canvas(device)
#    for X in ...:
#        with c as draw:
#            draw.rectangle(...)
#
# As before, as soon as the with block completes, the canvas buffer is flushed
# to the device

import atexit
from PIL import Image
from oled.serial import i2c
import oled.mixin as mixin


class device(mixin.capabilities):
    """
    Base class for OLED driver classes
    """
    def __init__(self, serial_interface=None):
        self._serial_interface = serial_interface or i2c()

        def cleanup():
            self.hide()
            self.clear()
            self._serial_interface.cleanup()

        atexit.register(cleanup)

    def command(self, *cmd):
        """
        Sends a command or sequence of commands through to the delegated
        serial interface.
        """
        assert(len(cmd) <= 32)
        self._serial_interface.command(*cmd)

    def data(self, data):
        """
        Sends a data byte or sequence of data bytes through to the delegated
        serial interface.
        """
        self._serial_interface.data(data)

    def show(self):
        """
        Sets the display mode ON, waking the device out of a prior
        low-power sleep mode.
        """
        self.command(const.DISPLAYON)

    def hide(self):
        """
        Switches the display mode OFF, putting the device in low-power
        sleep mode.
        """
        self.command(const.DISPLAYOFF)

    def clear(self):
        """
        Initializes the device memory with an empty (blank) image.
        """
        self.display(Image.new(self.mode, (self.width, self.height)))


class sh1106(device):
    """
    Encapsulates the serial interface to the SH1106 OLED display hardware. On
    creation, an initialization sequence is pumped to the display to properly
    configure it. Further control commands can then be called to affect the
    brightness and other settings.

    .. warning::
        Direct use of the :func:`command` and :func:`data` methods are
        discouraged: Screen updates should be effected through the
        :func:`display` method, or preferably with the
        :class:`oled.render.canvas` context manager.
    """

    def __init__(self, serial_interface=None, width=128, height=64):
        try:
            super(sh1106, self).__init__(serial_interface)
            self.capabilities(width, height)
            self.bounding_box = (0, 0, width - 1, height - 1)
            self.width = width
            self.height = height
            self._pages = self.height // 8

            self.command(
                const.DISPLAYOFF,
                const.MEMORYMODE,
                const.SETHIGHCOLUMN,      0xB0, 0xC8,
                const.SETLOWCOLUMN,       0x10, 0x40,
                const.SETCONTRAST,        0x7F,
                const.SETSEGMENTREMAP,
                const.NORMALDISPLAY,
                const.SETMULTIPLEX,       0x3F,
                const.DISPLAYALLON_RESUME,
                const.SETDISPLAYOFFSET,   0x00,
                const.SETDISPLAYCLOCKDIV, 0xF0,
                const.SETPRECHARGE,       0x22,
                const.SETCOMPINS,         0x12,
                const.SETVCOMDETECT,      0x20,
                const.CHARGEPUMP,         0x14)

            self.clear()
            self.show()

        except IOError as e:
            raise IOError(e.errno,
                          "Failed to initialize SH1106 display driver")

    def display(self, image):
        """
        Takes a 1-bit :py:mod:`PIL.Image` and dumps it to the SH1106
        OLED display.
        """
        assert(image.mode == self.mode)
        assert(image.size[0] == self.width)
        assert(image.size[1] == self.height)

        page = 0xB0
        pix = list(image.getdata())
        step = self.width * 8
        for y in range(0, self._pages * step, step):

            # move to given page, then reset the column address
            self.command(page, 0x02, 0x10)
            page += 1

            buf = []
            for x in range(self.width):
                byte = 0
                for n in range(0, step, self.width):
                    byte |= (pix[x + y + n] & 0x01) << 8
                    byte >>= 1

                buf.append(byte)

            self.data(buf)


class ssd1306(device):
    """
    Encapsulates the serial interface to the SSD1306 OLED display hardware. On
    creation, an initialization sequence is pumped to the display to properly
    configure it. Further control commands can then be called to affect the
    brightness and other settings.

    .. warning::
        Direct use of the :func:`command` and :func:`data` methods are
        discouraged: Screen updates should be effected through the
        :func:`display` method, or preferably with the
        :class:`oled.render.canvas` context manager.
    """
    def __init__(self, serial_interface=None, width=128, height=64):
        try:
            super(ssd1306, self).__init__(serial_interface)
            self.capabilities(width, height)
            self._pages = self.height // 8
            self._buffer = [0] * self.width * self._pages
            self._offsets = [n * self.width for n in range(8)]

            self.command(
                const.DISPLAYOFF,
                const.SETDISPLAYCLOCKDIV, 0x80,
                const.SETMULTIPLEX,       0x3F,
                const.SETDISPLAYOFFSET,   0x00,
                const.SETSTARTLINE,
                const.CHARGEPUMP,         0x14,
                const.MEMORYMODE,         0x00,
                const.SEGREMAP,
                const.COMSCANDEC,
                const.SETCOMPINS,         0x12,
                const.SETCONTRAST,        0xCF,
                const.SETPRECHARGE,       0xF1,
                const.SETVCOMDETECT,      0x40,
                const.DISPLAYALLON_RESUME,
                const.NORMALDISPLAY)

            self.clear()
            self.show()

        except IOError as e:
            raise IOError(e.errno,
                          "Failed to initialize SSD1306 display driver")

    def display(self, image):
        """
        Takes a 1-bit :py:mod:`PIL.Image` and dumps it to the SSD1306
        OLED display.
        """
        assert(image.mode == self.mode)
        assert(image.size[0] == self.width)
        assert(image.size[1] == self.height)

        self.command(
            # Column start/end address
            const.COLUMNADDR, 0x00, self.width - 1,
            # Page start/end address
            const.PAGEADDR, 0x00, self._pages - 1)

        pix = list(image.getdata())
        step = self.width * 8
        buf = self._buffer
        offsets = self._offsets
        w = self.width
        j = 0
        for y in range(0, self._pages * step, step):
            i = y + w - 1
            while i >= y:
                buf[j] = (pix[i] & 0x01) | \
                         (pix[i + offsets[1]] & 0x01) << 1 | \
                         (pix[i + offsets[2]] & 0x01) << 2 | \
                         (pix[i + offsets[3]] & 0x01) << 3 | \
                         (pix[i + offsets[4]] & 0x01) << 4 | \
                         (pix[i + offsets[5]] & 0x01) << 5 | \
                         (pix[i + offsets[6]] & 0x01) << 6 | \
                         (pix[i + offsets[7]] & 0x01) << 7

                i -= 1
                j += 1

        self.data(buf)


class const:
    CHARGEPUMP = 0x8D
    COLUMNADDR = 0x21
    COMSCANDEC = 0xC8
    COMSCANINC = 0xC0
    DISPLAYALLON = 0xA5
    DISPLAYALLON_RESUME = 0xA4
    DISPLAYOFF = 0xAE
    DISPLAYON = 0xAF
    EXTERNALVCC = 0x1
    INVERTDISPLAY = 0xA7
    MEMORYMODE = 0x20
    NORMALDISPLAY = 0xA6
    PAGEADDR = 0x22
    SEGREMAP = 0xA0
    SETCOMPINS = 0xDA
    SETCONTRAST = 0x81
    SETDISPLAYCLOCKDIV = 0xD5
    SETDISPLAYOFFSET = 0xD3
    SETHIGHCOLUMN = 0x10
    SETLOWCOLUMN = 0x00
    SETMULTIPLEX = 0xA8
    SETPRECHARGE = 0xD9
    SETSEGMENTREMAP = 0xA1
    SETSTARTLINE = 0x40
    SETVCOMDETECT = 0xDB
    SWITCHCAPVCC = 0x2
