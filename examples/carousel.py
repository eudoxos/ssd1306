#!/usr/bin/env python
# -*- coding: utf-8 -*-

from demo_opts import device
from oled.virtual import viewport, snapshot
import hotspot.memory as memory
import hotspot.cpu_load as cpu_load
import hotspot.clock as clock
import hotspot.network as network
import hotspot.disk as disk


def position(max):
    forwards = range(0, max)
    backwards = range(max, 0, -1)
    while True:
        for x in forwards:
            yield x
        for x in backwards:
            yield x


def pause_every(interval, generator):
    try:
        while True:
            x = generator.next()
            if x % interval == 0:
                for _ in range(20):
                    yield x
            else:
                yield x
    except StopIteration:
        pass


if __name__ == "__main__":

    virtual = viewport(device, width=64 * 6, height=64)

    # Either function or subclass
    #  cpuload = hotspot(64, 64, cpu_load.render)
    #  cpuload = cpu_load.CPU_Load(64, 64, interval=1.0)
    memory = snapshot(64, 64, memory.render, interval=2.0)
    disk = snapshot(64, 64, disk.render, interval=2.0)
    cpuload = snapshot(64, 64, cpu_load.render, interval=0.5)
    clock = snapshot(64, 64, clock.render, interval=1.0)
    net_wlan0 = snapshot(64, 64, network.stats("en0"), interval=2.0)
    net_lo = snapshot(64, 64, network.stats("lo0"), interval=2.0)

    virtual.add_hotspot(cpuload, (0, 0))
    virtual.add_hotspot(clock, (64, 0))
    virtual.add_hotspot(net_wlan0, (128, 0))
    virtual.add_hotspot(net_lo, (192, 0))
    virtual.add_hotspot(memory, (256, 0))
    virtual.add_hotspot(disk, (320, 0))

    for x in pause_every(64, position(64 * 4)):
        virtual.set_position((x, 0))
