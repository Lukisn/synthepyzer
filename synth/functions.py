#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from numpy import sin, pi, sign, arcsin, arctan, tan


# standard waves:
def sine(time, freq=1, amp=1, phase=0):
    assert freq >= 0
    assert amp >= 0
    return amp * sin(2 * pi * freq * time + phase)


def square(time, freq=1, amp=1):
    assert freq >= 0
    assert amp >= 0
    return amp * sign(sine(time, freq=freq))


def triangle(time, freq=1, amp=1):
    assert freq >= 0
    assert amp >= 0
    return 2 * amp / pi * arcsin(sin(2 * pi * freq * time))


def saw(time, freq=1, amp=1):
    assert freq >= 0
    assert amp >= 0
    return -2 * amp / pi * arctan(1 / tan(pi * freq * time))


# special waves:
def pulse(time, freq=1, amp=1, shift=0):
    assert freq >= 0
    assert amp >= 0
    assert -1 <= shift <= 1
    return amp * sign(sine(time, freq=freq) + shift * amp)


# envelopes:
def adsr_envelope(time, attack, decay, sustain, release):
    pass  # TODO
