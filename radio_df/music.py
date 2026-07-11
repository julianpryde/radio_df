"""MUSIC (MUltiple SIgnal Classification) angle-of-arrival estimation.

Takes an arbitrary number of I/Q input feeds and determines the arrival paths
of all signals. Requires a pre-defined number of expected received signals.

Only works for one frequency at a time, so D usually = 1. D would only be > 1
for multiple arrival paths of the same signal or two stations transmitting on
the same frequency.

Original step outline adapted from:
https://www.cs.princeton.edu/courses/archive/spring18/cos463/labs/lab5_preview.html
That lab uses a uniform linear array, which only resolves -90..+90 degrees;
this project uses a uniform circular array for full 360-degree coverage.
"""
import numpy as np


def music(received_signal, num_signals, num_antennae):
    # 1. compute the correlation matrix of the received signal.
    # the expected output matrix should be a [MxM] matrix

    # 2. Compute the eigenvalues and the eigenvectors of the correlation
    # matrix with numpy.linalg.eigh.

    # 3. Sort the eigenvalues and eigenvectors, extracting the eigenvectors
    # corresponding to the noise subspace.

    # 4. Define the steering vector a(theta) for a uniform circular array,
    # parameterized by carrier frequency and array radius.

    # 5. Loop over the bearing from 0 to 360 degrees in one degree increments
    # and compute the pseudo spectrum.

    p_spectrum = np.zeros(360)
    return p_spectrum
