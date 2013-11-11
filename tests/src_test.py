#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  resample_test.py
#
#

import sys

sys.path.append('../')

import numpy as np
import scikits.samplerate as sr
from matplotlib import pyplot as plt

import src

N = 100
CHANS = 3
rate = .5
Q = 'sinc_fastest'

orig_seq = np.random.randn(N, CHANS)

resampled1 = sr.resample(orig_seq, rate, Q)

rsampler = src.Resampler(src.SINC_FASTEST, channels = CHANS, default_ratio = rate)

resampled2A, ifu = rsampler.process(orig_seq[:N/2,:], end_of_input = False)
print ifu
resampled2B, ifu = rsampler.process(orig_seq[N/2:,:], end_of_input = False)
print ifu
resampled3B, ifu = rsampler.end_input()
print ifu

resampled2 = np.concatenate([resampled2A, resampled2B, resampled3B])
#resampled2 = resampled2A
print resampled1.shape, resampled2.shape, resampled3B.shape

plt.hold(True)
plt.plot(resampled1, 'b')
plt.plot(resampled2, 'g-')

plt.show()
