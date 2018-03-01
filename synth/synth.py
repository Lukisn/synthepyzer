#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from signal import signal, SIGINT

from numpy import linspace, iinfo, int8, int16, int32
from pyaudio import paInt8, paInt16, paInt32, paContinue, PyAudio

from functions import sine, square, triangle, saw

# from matplotlib.pyplot import plot, show


# def sine_table(freq, amp, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period-sample_size, samples-1)
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     ang_vel = 2 * pi * freq  # angular velocity
#     sine = (amp_mul * sin(ang_vel * time)).astype(np_dtype)
#
#     # plot(sine)
#     # show()
#
#     sine_bytes = sine.tobytes()
#     return sine_bytes
#
#
# def rect_table(freq, amp, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period - sample_size, samples - 1)
#
#     def rect_func(x, freq, amp):
#         period = 1 / freq
#         x = x % period
#         half = period / 2
#         if x < half:
#             return amp
#         return -amp
#     rect_func_vec = vectorize(rect_func)
#
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     rect = rect_func_vec(time, freq, amp_mul).astype(np_dtype)
#
#     # plot(rect)
#     #show()
#
#     rect_bytes = rect.tobytes()
#     return rect_bytes
#
#
# def pwm_table(freq, amp, width, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period - sample_size, samples - 1)
#
#     def pwm_func(x, freq, amp, width):
#         period = 1 / freq
#         x = x % period
#         half = width * period
#         if x < half:
#             return amp
#         return -amp
#     pwm_func_vec = vectorize(pwm_func)
#
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     pwm = pwm_func_vec(time, freq, amp_mul, width).astype(np_dtype)
#
#     # plot(pwm)
#     # show()
#
#     pwm_bytes = pwm.tobytes()
#     return pwm_bytes
#
#
# def saw_up_table(freq, amp, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period - sample_size, samples - 1)
#
#     def saw_up(x, freq, amp):
#         period = 1 / freq
#         x = x % period
#         half = period / 2
#         if x < half:
#             return amp * (x / half)
#         return amp * ((x - half) / half - 1)
#     saw_up_vec = vectorize(saw_up)
#
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     saw_up = saw_up_vec(time, freq, amp_mul).astype(np_dtype)
#
#     # plot(saw_up)
#     # show()
#
#     saw_up_bytes = saw_up.tobytes()
#     return saw_up_bytes
#
#
# def saw_down_table(freq, amp, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period - sample_size, samples - 1)
#
#     def saw_down(x, freq, amp):
#         period = 1 / freq
#         x = x % period
#         half = period / 2
#         if x < half:
#             return -amp * (x / half)
#         return -amp * ((x - half) / half - 1)
#     saw_down_vec = vectorize(saw_down)
#
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     saw_down = saw_down_vec(time, freq, amp_mul).astype(np_dtype)
#
#     # plot(saw_down)
#     # show()
#
#     saw_down_bytes = saw_down.tobytes()
#     return saw_down_bytes
#
#
# def triangle_table(freq, amp, rate, np_dtype):
#     sample_size = 1 / rate
#     period = 1 / freq  # s
#     samples = round(period / sample_size)  # samples per period
#     time = linspace(0, period - sample_size, samples - 1)
#
#     def triangle(x, freq, amp):
#         period = 1 / freq
#         x = x % period
#         quart = period / 4
#         if x < quart:
#             return amp * x / quart
#         if x > 3 * quart:
#             return amp * ((x - 3*quart) / quart - 1)
#         return -amp * ((x - quart) / quart - 1)
#
#     triangle_vec = vectorize(triangle)
#
#     amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
#     triangle = triangle_vec(time, freq, amp_mul).astype(np_dtype)
#
#     # plot(triangle)
#     # show()
#
#     triangle_bytes = triangle.tobytes()
#     return triangle_bytes


def table(func, freq, amp, rate, dtype):
    sample_time = 1 / rate  # duration of a single sample (s)
    period = 1 / freq  # period of the wave (s)
    samples = round(period / sample_time)  # samples per period (-)
    time = linspace(0, period - sample_time, samples - 1)
    amp = amp * iinfo(dtype).max  # amplitude multiplier
    wave = func(time, freq=freq, amp=amp).astype(dtype)
    return wave.tobytes()


class RingBuffer:

    def __init__(self, buf, width):
        self.buffer = buf  # buffer to cycle through
        self.sample_width = width  # sample width in bytes
        self.length = len(self.buffer)  # length of a single buffer cycle
        self.pos = 0  # current position in the buffer

    def readframes(self, frames):
        result = b""  # resulting output to compute
        samples = frames * self.sample_width
        samples_left = self.length - self.pos  # frames left in table

        if samples <= samples_left:  # only read needed frames and proceed pos
            result += self.buffer[self.pos:self.pos+samples]
            self.pos += samples
        else:  # read all frames left, cycle through buffer to fill frames
            # add all frames left:
            result += self.buffer[self.pos:]
            samples -= samples_left
            self.pos = 0
            # add full chunks:
            cycles = samples // self.length
            rest = samples % self.length
            for _ in range(cycles):
                result += self.buffer
            # add remaining left frames
            result += self.buffer[self.pos:rest]
            self.pos += rest
        return result

    def reset(self):
        self.pos = 0


class Instrument:

    def __init__(self):
        self.tuning = 440  # A4 tuning
        self.current = "C0"
        self.notes = {
            "C0": None,  # TODO
            "D0": None,
            "E0": None,
            "F0": None,
            "G0": None,
            "A0": None,
            "B0": None,
            "C1": None,
            # ...
        }

    def readframes(self, note, frames):
        return self.notes[note].readframes(frames)

    def reset(self):
        for note in self.notes:
            note.reset()


def main():
    # general:
    srate = 96000  # Hz (number of samples per second)
    swidth = 4  # number of bytes per sample

    if swidth == 1:
        np_dtype = int8
        audio_fmt = paInt8
    elif swidth == 2:
        np_dtype = int16
        audio_fmt = paInt16
    elif swidth == 4:
        np_dtype = int32
        audio_fmt = paInt32
    else:
        raise NotImplementedError("Only 8, 16 and 32 bit samples implemented")

    # wave:
    amp = 0.3  # 0..1 (%)
    freq = 220  # Hz
    sine_table = table(func=sine, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    square_table = table(func=square, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    triangle_table = table(func=triangle, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    saw_table = table(func=saw, freq=freq, amp=amp, rate=srate, dtype=np_dtype)

    sine_buffer = RingBuffer(buf=sine_table, width=swidth)
    square_buffer = RingBuffer(buf=square_table, width=swidth)
    triangle_buffer = RingBuffer(buf=triangle_table, width=swidth)
    saw_buffer = RingBuffer(buf=saw_table, width=swidth)

    def callback(in_data, frame_count, time_info, status):
        data = square_buffer.readframes(frame_count)
        return data, paContinue

    audio = PyAudio()
    stream = audio.open(
        format=audio_fmt,  # sample width
        channels=1,  # number of channels 1=mono, 2=stereo
        rate=srate,  # sample rate
        output=True,
        stream_callback=callback)

    def handler(signum, frame):
        print('Signal handler called with signal', signum)
        stream.stop_stream()

    signal(SIGINT, handler)

    stream.start_stream()
    while stream.is_active():
        sleep(0.1)
    stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == "__main__":
    main()
