#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from re import match
from signal import signal, SIGINT
from time import sleep

from numpy import linspace, iinfo, int8, int16, int32
from pyaudio import paInt8, paInt16, paInt32, paContinue, PyAudio
import pygame

from synthepyzer.functions import sine, square, triangle, saw

pygame.init()

notes = {  # semitone offsets
        "C": -9,
        "C#": -8, "Db": -8,
        "D": -7,
        "D#": -6, "Eb": -6,
        "E": -5,
        "F": -4,
        "F#": -3, "Gb": -3,
        "G": -2,
        "G#": -1, "Ab": -1,
        "A": 0,
        "A#": 1, "Bb": 1,
        "B": 2,
    }


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


def note_freq(notename, base_freq=440, base_oct=4):
    pattern = r"(?P<note>[ABCDEFGH])(?P<mod>[#b]*)(?P<oct>-*\d*)"
    matched = match(pattern, notename)
    if not matched:
        raise ValueError(f"invalid note name '{notename}'")
    note = matched.group("note") + matched.group("mod")
    octave = int(matched.group("oct"))
    offset = 12 * (octave - base_oct) + notes[note]
    freq = base_freq * 2 ** (offset / 12)
    return freq


class Oscillator:

    def __init__(self, wave_func):
        self.notes = {}
        for octave in range(0, 9):
            for note in notes:
                notename = note + str(octave)
                wave_table = table(func=wave_func, freq=note_freq(notename),
                                   amp=1, rate=96000, dtype=int32)
                wave_buffer = RingBuffer(buf=wave_table, width=4)
                self.notes[notename] = wave_buffer
        self.current_note = "A"
        self.current_octave = 4

    def current(self):
        return self.current_note + str(self.current_octave)

    def readframes(self, frames):
        return self.notes[self.current()].readframes(frames)

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
    # amp = 0.3  # 0..1 (%)
    # freq = note_freq("C4")  # 220  # Hz
    # print(freq)
    # sine_table = table(func=sine, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    # square_table = table(func=square, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    # triangle_table = table(func=triangle, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    # saw_table = table(func=saw, freq=freq, amp=amp, rate=srate, dtype=np_dtype)
    # sine_buffer = RingBuffer(buf=sine_table, width=swidth)
    # square_buffer = RingBuffer(buf=square_table, width=swidth)
    # triangle_buffer = RingBuffer(buf=triangle_table, width=swidth)
    # saw_buffer = RingBuffer(buf=saw_table, width=swidth)q

    osc = Oscillator(wave_func=saw)
    print(osc.notes)

    def callback(in_data, frame_count, time_info, status):
        # data = triangle_buffer.readframes(frame_count)
        data = osc.readframes(frames=frame_count)
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
    running = True
    while running and stream.is_active():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                print(f"pressed {event.key} ('{event.unicode}') mod = {event.mod}")
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_a:
                    osc.current_note = "C"
                elif event.key == pygame.K_s:
                    osc.current_note = "D"
                elif event.key == pygame.K_d:
                    osc.current_note = "E"
                elif event.key == pygame.K_f:
                    osc.current_note = "F"
                elif event.key == pygame.K_g:
                    osc.current_note = "G"
                elif event.key == pygame.K_h:
                    osc.current_note = "A"
                elif event.key == pygame.K_j:
                    osc.current_note = "B"
                elif event.key == pygame.K_PLUS:
                    osc.current_octave += 1
                elif event.key == pygame.K_MINUS:
                    osc.current_octave -= 1
            elif event.type == pygame.KEYUP:
                print(f"released {event.key} mod = {event.mod}")
    stream.stop_stream()
    stream.close()
    audio.terminate()


if __name__ == "__main__":
    main()

