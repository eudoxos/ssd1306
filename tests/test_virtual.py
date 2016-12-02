#!/usr/bin/env python
# -*- coding: utf-8 -*-

from oled.virtual import range_overlap


def overlap(box1, box2):
    l1, t1, r1, b1 = box1
    l2, t2, r2, b2 = box2
    return range_overlap(l1, r1, l2, r2) and range_overlap(t1, b1, t2, b2)


box1 = [0, 0, 64, 64]
box2 = [64, 0, 128, 64]
box3 = [128, 0, 192, 64]
box4 = [192, 0, 256, 64]


def test_range_overlap_over12():
    viewport = [0, 0, 128, 64]
    assert overlap(viewport, box1) is True
    assert overlap(viewport, box2) is True
    assert overlap(viewport, box3) is False
    assert overlap(viewport, box4) is False


def test_range_overlap_over123():
    viewport = [30, 0, 158, 64]
    assert overlap(viewport, box1) is True
    assert overlap(viewport, box2) is True
    assert overlap(viewport, box3) is True
    assert overlap(viewport, box4) is False


def test_range_overlap_over23():
    viewport = [64, 0, 192, 64]
    assert overlap(viewport, box1) is False
    assert overlap(viewport, box2) is True
    assert overlap(viewport, box3) is True
    assert overlap(viewport, box4) is False


def test_range_overlap_over234():
    viewport = [100, 0, 228, 64]
    assert overlap(viewport, box1) is False
    assert overlap(viewport, box2) is True
    assert overlap(viewport, box3) is True
    assert overlap(viewport, box4) is True


def test_range_overlap_over34():
    viewport = [128, 0, 256, 64]
    assert overlap(viewport, box1) is False
    assert overlap(viewport, box2) is False
    assert overlap(viewport, box3) is True
    assert overlap(viewport, box4) is True


def test_range_overlap_over4():
    viewport = [192, 0, 256, 64]
    assert overlap(viewport, box1) is False
    assert overlap(viewport, box2) is False
    assert overlap(viewport, box3) is False
    assert overlap(viewport, box4) is True


def test_range_overlap_over_none():
    viewport = [256, 0, 384, 64]
    assert overlap(viewport, box1) is False
    assert overlap(viewport, box2) is False
    assert overlap(viewport, box3) is False
    assert overlap(viewport, box4) is False
