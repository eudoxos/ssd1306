#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import datetime


def posn(angle, arm_length):
    dx = int(math.cos(math.radians(angle)) * arm_length)
    dy = int(math.sin(math.radians(angle)) * arm_length)
    return (dx, dy)


def render(draw, width, height):
    now = datetime.datetime.now()
    today_date = now.strftime("%d %b %y")

    top = 14
    margin = 2

    cx = width / 2
    cy = top + ((height - top - margin) / 2)

    left = (width - (height - top - margin)) / 2
    right = width - left

    hrs_angle = 270 + (30 * (now.hour + (now.minute / 60.0)))
    hrs = posn(hrs_angle, cx - 16)

    min_angle = 270 + (6 * now.minute)
    mins = posn(min_angle, cx - 10)

    sec_angle = 270 + (6 * now.second)
    secs = posn(sec_angle, cx - 10)

    draw.ellipse((left, top, right, height - margin), outline="white")
    draw.line((cx, cy, cx + hrs[0], cy + hrs[1]), fill="white")
    draw.line((cx, cy, cx + mins[0], cy + mins[1]), fill="white")
    draw.line((cx, cy, cx + secs[0], cy + secs[1]), fill="white")
    draw.text((7, 3), today_date, fill="white")
