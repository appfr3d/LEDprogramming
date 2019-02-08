# -*- coding: utf-8 -*-
import time
from neopixel import *
import pyaudio
import numpy as np


# Setup
LED_COUNT      = 300
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 5
LED_BRIGHTNESS = 255
LED_INVERT     = False


np.set_printoptions(suppress=True)

CHUNK = 4096
RATE = 44100

MAX_VOLUME = 500000000
MIN_VOLUME = 1000000


def getRGB(data):
	data = data * np.hanning(len(data))
	fft = abs(np.fft.fft(data).real)
	fft = fft[:int(len(fft)/2)] # keep only the first half
	# freq = np.fft.fftfreq(CHUNK, 1.0/RATE)
	# freq = freq[:int(len(freq)/2)] # keep only the first half

	sums = [part.sum() for part in np.split(fft, [21, 201])]
	rgb = [int(np.interp(part, [0, sum(sums)], [0, 255])) for part in sums]
	return rgb

def getRGBAndSoundLevel(data):
	data = data * np.hanning(len(data))
        fft = abs(np.fft.fft(data).real)
        fft = fft[:int(len(fft)/2)] # keep only the first half

	# Base the rgb on how much og each range, but also based on the highest freq in each range
	# ranges = np.split(fft, [21, 201])

        sums = [part.sum() for part in np.split(fft, [21, 201])]
        rgb = [int(np.interp(part, [0, sum(sums)], [0, 255])) for part in sums]

	rgb = [rgb[1], rgb[0], rgb[2]]
	# Based on only the bass
	# bass = int(np.interp(sums[0], [0, sum(sums)], [0, 255]))
	# Ia really grb...
	# rgb = [0, 0, bass]
	# Makes a form for sound level
	soundLevel = sum(sums)

	return [rgb, soundLevel]

def setColor(strip, color, wait_ms=10):
        for i in range(strip.numPixels()):
                strip.setPixelColor(i, color)
	strip.show()
        time.sleep(wait_ms/1000.0)

def setColorAndSoundLevel(strip, color, num, wait_ms=10):
	mid = int(LED_COUNT/2)

	# Set color in the middle, based on num
	for i in range(num):
		strip.setPixelColor(mid+i, color)
		strip.setPixelColor(mid-i-1, color)

	# Set no color on the others
	for i in range(int(LED_COUNT/2)-num):
		strip.setPixelColor(i, Color(0,0,0))
		strip.setPixelColor(LED_COUNT-i-1, Color(0,0,0))
	strip.show()
	# time.sleep(wait_ms/1000.0)

def clearColors(strip):
        for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(0,0,0))
        strip.show()


# Main program logic
if __name__ == "__main__":
        # Create Neopixel object
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

        # Initialize libary
        strip.begin()

	# Start the PyAudio class
	p = pyaudio.PyAudio()

	# Uses default input device
	stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

	lastNum = [0]*5
	try:
		while True:
			data = np.frombuffer(stream.read(CHUNK),dtype=np.int16)

			# Uncomment to set all pixels to same color
			# rgb = getRGB(data)
			# print rgb
			# setColor(strip, Color(rgb[0], rgb[1], rgb[2]))

			# Uncomment to set color on a number of pixels from the middle and out based on the

			high = 700000000 # (seven hundred million)
			low = 1000000    # (one million)

			rgb, soundLevel = getRGBAndSoundLevel(data)

			soundLevel = max(MIN_VOLUME, min(soundLevel, MAX_VOLUME))
			num = int(np.interp(soundLevel, [MIN_VOLUME, MAX_VOLUME], [0, int(LED_COUNT/2)]))
			# print num
			# n = int((num + lastNum)/2)

			# lastNum = num
			# Average the 10 last volume levels
			for i in range(len(lastNum)-1, 1, -1):
				lastNum[i] = lastNum[i-1]

			lastNum[0] = num

			n = int(sum(lastNum)/len(lastNum))

			# setColorAndSoundLevel(strip, Color(rgb[0], rgb[1], rgb[2]), n, 10)
			setColor(strip, Color(rgb[0], rgb[1], rgb[2]))
			# setColorAndSoundLevel(strip, Color(rgb[0], rgb[1], rgb[2]), num, 100)

	except KeyboardInterrupt:
		print 'interrupted!'


	clearColors(strip)
	stream.stop_stream()
	stream.close()
	p.terminate()
