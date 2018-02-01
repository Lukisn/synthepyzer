#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from signal import signal, SIGINT

from numpy import pi, sin, linspace, iinfo, int8, int16, int32, vectorize
from pyaudio import paInt8, paInt16, paInt32, paContinue, PyAudio

# from matplotlib.pyplot import plot, show


def sine_table(freq, amp, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period-sample_size, samples-1)
    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    ang_vel = 2 * pi * freq  # angular velocity
    sine = (amp_mul * sin(ang_vel * time)).astype(np_dtype)

    # plot(sine)
    # show()

    sine_bytes = sine.tobytes()
    return sine_bytes


def rect_table(freq, amp, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period - sample_size, samples - 1)

    def rect_func(x, freq, amp):
        period = 1 / freq
        x = x % period
        half = period / 2
        if x < half:
            return amp
        return -amp
    rect_func_vec = vectorize(rect_func)

    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    rect = rect_func_vec(time, freq, amp_mul).astype(np_dtype)

    # plot(rect)
    #show()

    rect_bytes = rect.tobytes()
    return rect_bytes


def pwm_table(freq, amp, width, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period - sample_size, samples - 1)

    def pwm_func(x, freq, amp, width):
        period = 1 / freq
        x = x % period
        half = width * period
        if x < half:
            return amp
        return -amp
    pwm_func_vec = vectorize(pwm_func)

    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    pwm = pwm_func_vec(time, freq, amp_mul, width).astype(np_dtype)

    # plot(pwm)
    # show()

    pwm_bytes = pwm.tobytes()
    return pwm_bytes


def saw_up_table(freq, amp, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period - sample_size, samples - 1)

    def saw_up(x, freq, amp):
        period = 1 / freq
        x = x % period
        half = period / 2
        if x < half:
            return amp * (x / half)
        return amp * ((x - half) / half - 1)
    saw_up_vec = vectorize(saw_up)

    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    saw_up = saw_up_vec(time, freq, amp_mul).astype(np_dtype)

    # plot(saw_up)
    # show()

    saw_up_bytes = saw_up.tobytes()
    return saw_up_bytes


def saw_down_table(freq, amp, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period - sample_size, samples - 1)

    def saw_down(x, freq, amp):
        period = 1 / freq
        x = x % period
        half = period / 2
        if x < half:
            return -amp * (x / half)
        return -amp * ((x - half) / half - 1)
    saw_down_vec = vectorize(saw_down)

    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    saw_down = saw_down_vec(time, freq, amp_mul).astype(np_dtype)

    # plot(saw_down)
    # show()

    saw_down_bytes = saw_down.tobytes()
    return saw_down_bytes


def triangle_table(freq, amp, rate, np_dtype):
    sample_size = 1 / rate
    period = 1 / freq  # s
    samples = round(period / sample_size)  # samples per period
    time = linspace(0, period - sample_size, samples - 1)

    def triangle(x, freq, amp):
        period = 1 / freq
        x = x % period
        quart = period / 4
        if x < quart:
            return amp * x / quart
        if x > 3 * quart:
            return amp * ((x - 3*quart) / quart - 1)
        return -amp * ((x - quart) / quart - 1)

    triangle_vec = vectorize(triangle)

    amp_mul = amp * iinfo(np_dtype).max  # amplitude multiplier
    triangle = triangle_vec(time, freq, amp_mul).astype(np_dtype)

    # plot(triangle)
    # show()

    triangle_bytes = triangle.tobytes()
    return triangle_bytes


class RingBuffer:

    def __init__(self, buf, width):
        self.buffer = buf  # buffer to cycle through
        self.sample_width = width  # sample width in bytes
        self.length = len(self.buffer)  # length of a single buffer cycle
        self.pos = 0  # current position in the buffer

    def read(self, frames):
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


def main():
    # general:
    sample_rate = 96000  # Hz (number of samples per second)
    sample_width = 4  # number of bytes per sample

    if sample_width == 1:
        numpy_dtype = int8
        audio_format = paInt8
    elif sample_width == 2:
        numpy_dtype = int16
        audio_format = paInt16
    elif sample_width == 4:
        numpy_dtype = int32
        audio_format = paInt32
    else:
        raise NotImplementedError("Only 8, 16 and 32 bit samples implemented")

    # wave:
    amplitude = 0.3  # 0..1 (%)
    frequency = 110  # Hz
    width = 0.1
    sine_bytes = sine_table(freq=frequency, amp=amplitude, rate=sample_rate, np_dtype=numpy_dtype)
    lfo_bytes = sine_table(freq=10, amp=1.0, rate=sample_rate, np_dtype=numpy_dtype)
    rect_bytes = rect_table(freq=frequency, amp=amplitude, rate=sample_rate, np_dtype=numpy_dtype)
    pwm_bytes = pwm_table(freq=frequency, amp=amplitude, width=width, rate=sample_rate, np_dtype=numpy_dtype)
    saw_up_bytes = saw_up_table(freq=frequency, amp=amplitude, rate=sample_rate, np_dtype=numpy_dtype)
    saw_down_bytes = saw_down_table(freq=frequency, amp=amplitude, rate=sample_rate, np_dtype=numpy_dtype)
    triangle_bytes = triangle_table(freq=frequency, amp=amplitude, rate=sample_rate, np_dtype=numpy_dtype)
    sine_buffer = RingBuffer(buf=sine_bytes, width=sample_width)
    lfo_buffer = RingBuffer(buf=lfo_bytes, width=sample_width)
    rect_buffer = RingBuffer(buf=rect_bytes, width=sample_width)
    pwm_buffer = RingBuffer(buf=pwm_bytes, width=sample_width)
    saw_up_buffer = RingBuffer(buf=saw_up_bytes, width=sample_width)
    saw_down_buffer = RingBuffer(buf=saw_down_bytes, width=sample_width)
    triangle_buffer = RingBuffer(buf=triangle_bytes, width=sample_width)


    def callback(in_data, frame_count, time_info, status):
        data = sine_buffer.read(frame_count)
        # TODO: construct sound in callback from raw data
        # lfo = lfo_buffer.read(frame_count)
        # data *= lfo
        return (data, paContinue)

    audio = PyAudio()
    stream = audio.open(
        format=audio_format,  # sample width
        channels=1,  # number of channels 1=mono, 2=stereo
        rate=sample_rate,  # sample rate
        output=True,
        stream_callback=callback)

    def handler(signum, frame):
        print('Signal handler called with signal', signum)
        stream.stop_stream()

    signal(SIGINT, handler)

    stream.start_stream()
    while stream.is_active():
        sleep(0.1)
    # stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == "__main__":
    main()
