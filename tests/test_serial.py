#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from unittest.mock import patch, call, Mock
except ImportError:
    from mock import patch, call, Mock

import smbus2
from oled.serial import i2c, spi

smbus = Mock()
spidev = Mock()
gpio = Mock()


def setup_function(function):
    smbus.reset_mock()
    spidev.reset_mock()
    gpio.reset_mock()
    gpio.BCM = 1
    gpio.RST = 2
    gpio.DC = 3
    gpio.OUT = 4
    gpio.HIGH = 5
    gpio.LOW = 6


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


def test_i2c_init_no_bus():
    with patch.object(smbus2.SMBus, 'open') as mock:
        i2c(port=2, address=0x71)
    mock.assert_called_once_with(2)


def test_i2c_init_bus_provided():
    i2c(bus=smbus, address=0x71)
    smbus.open.assert_not_called()


def test_i2c_command():
    cmds = [3, 1, 4, 2]
    serial = i2c(bus=smbus, address=0x83)
    serial.command(*cmds)
    smbus.write_i2c_block_data.assert_called_once_with(0x83, 0x00, cmds)


def test_i2c_data():
    data = list(fib(10))
    serial = i2c(bus=smbus, address=0x21)
    serial.data(data)
    smbus.write_i2c_block_data.assert_called_once_with(0x21, 0x40, data)


def test_i2c_data_chunked():
    data = list(fib(100))
    serial = i2c(bus=smbus, address=0x66)
    serial.data(data)
    calls = [call(0x66, 0x40, data[i:i + 32]) for i in range(0, 100, 32)]
    smbus.write_i2c_block_data.assert_has_calls(calls)


def test_i2c_cleanup():
    serial = i2c(bus=smbus, address=0x9F)
    serial.cleanup()
    smbus.close.assert_called_once()


def verify_spi_init(port, device, bus_speed=8000000, dc=24, rst=25):
    spidev.open.assert_called_once_with(port, device)
    assert spidev.max_speed_hz == bus_speed
    gpio.setmode.assert_called_once_with(gpio.BCM)
    gpio.setup.assert_has_calls([call(dc, gpio.OUT), call(rst, gpio.OUT)])


def test_spi_init():
    spi(gpio=gpio, spi=spidev, port=5, device=2, bus_speed_hz=942312, bcm_DC=17, bcm_RST=11)
    verify_spi_init(5, 2, 942312, 17, 11)
    gpio.output.assert_called_once_with(11, gpio.HIGH)


def test_spi_command():
    cmds = [3, 1, 4, 2]
    serial = spi(gpio=gpio, spi=spidev, port=9, device=1)
    serial.command(*cmds)
    verify_spi_init(9, 1)
    gpio.output.assert_has_calls([call(25, gpio.HIGH), call(24, gpio.LOW)])
    spidev.xfer2.assert_called_once_with(cmds)


def test_spi_data():
    data = list(fib(100))
    serial = spi(gpio=gpio, spi=spidev, port=9, device=1)
    serial.data(data)
    verify_spi_init(9, 1)
    gpio.output.assert_has_calls([call(25, gpio.HIGH), call(24, gpio.HIGH)])
    spidev.xfer2.assert_called_once_with(data)


def test_spi_cleanup():
    serial = spi(gpio=gpio, spi=spidev, port=9, device=1)
    serial.cleanup()
    verify_spi_init(9, 1)
    spidev.close.assert_called_once()
    gpio.cleanup.assert_called_once()
