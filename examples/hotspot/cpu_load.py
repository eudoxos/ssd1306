#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import psutil
from oled.virtual import hotspot


def vertical_bar(draw, x1, y1, x2, y2, yh):
    draw.rectangle((x1, y1) + (x2, y2), "black", "white")
    draw.rectangle((x1, yh) + (x2, y2), "white", "white")


def render(draw, width, height):
    percentages = psutil.cpu_percent(interval=None, percpu=True)

    top_margin = 3
    bottom_margin = 3
    draw.text((8, top_margin), text="CPU Load", fill="white")

    bar_height = height - 15 - top_margin - bottom_margin
    width_cpu = width / len(percentages)
    bar_width = 0.5 * width_cpu
    bar_margin = (width_cpu - bar_width) / 2

    x = bar_margin

    for cpu in percentages:
        cpu_height = bar_height * (cpu / 100.0)
        y2 = height - bottom_margin
        vertical_bar(draw,
                     x, y2 - bar_height - 1,
                     x + bar_width, y2, y2 - cpu_height)

        x += width_cpu


class CPU_Load(hotspot):

    def __init__(self, width, height, interval):
        super(CPU_Load, self).__init__(width, height)
        self._interval = interval
        self._last_updated = 0

    def should_redraw(self):
        return time.time() - self._last_updated > self._interval

    def update(self, draw):
        render(draw, self.width, self.height)
        self._last_updated = time.time()
