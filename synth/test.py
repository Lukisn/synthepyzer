"""PyAudio Example: Play a wave file (callback version)."""

import pyaudio
import wave
import time
import sys

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')

print("channels:", wf.getnchannels())
print("sample width:", wf.getsampwidth())
print("frame rate:", wf.getframerate())
print("frames:", wf.getnframes())

print("1st frame:", wf.readframes(1))
sys.exit()

# instantiate PyAudio (1)
p = pyaudio.PyAudio()

# define callback (2)
def callback(in_data, frame_count, time_info, status):
    print("in data:", in_data)
    print("frame count:", frame_count)
    print("time info:", time_info)
    print("status:", status)
    data = wf.readframes(frame_count)
    print(len(data))
    # data = b"\x01" * frame_count
    # print(data)
    return (data, pyaudio.paContinue)

# open stream using callback (3)
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                stream_callback=callback)

# start the stream (4)
stream.start_stream()

# wait for stream to finish (5)
while stream.is_active():
    time.sleep(0.1)

# stop stream (6)
stream.stop_stream()
stream.close()
wf.close()

# close PyAudio (7)
p.terminate()
