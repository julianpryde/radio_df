"""
Takes an arbitrary number of I/Q input feeds and determines an arrival paths of
all signals. Requires pre-defined number of expected received signals.

Only works for one frequency at a time, so D usually = 1. D otherwise would only
be > 1 for multiple arrival paths of the same signal or two stations
transmitting on the same frequency.

MUltiple Signal Classification
MUSIC_algo taken from: https://www.cs.princeton.edu/courses/archive/spring18/cos463/labs/lab5_preview.html#:~:text=Angle%20of%20arrival%20%28AoA%29%20measurement%20is%20a%20method,from%20these%20difference%20the%20AoA%20can%20be%20calculated.
"""
import numpy as np

def music(received_signal, num_signals, num_antennae):
    # the wavelength of the wireless signal
    c = 3e8
    channel_freq = 2.442e9
    wavelength = c / channel_freq

    # antenna spacing: half lambda
    antenna_spacing = wavelength / 2

    # 1. compute the correlation matrix of the received signal.
    # the expected output matrix should be a [MxM] matrix


    # 2. Compute the eigenvalues and the eigenvectors of the correlation matrix.
    # You can use the numpy API to get the eigenvectors and eigenvalues: numpy.linalg.eigh(input).

    # 3. sorting the eigenvalues and eigenvectors, extracting the eigenvectors correspond to the noises.

    # 4. Define the steering vector (referring to the defination of a(theta)).
    # The spacing between adjacent antennas is LAMBDA/2.

    # 5. loop over the angle from -90 to 90 degrees in one degree increments, and compute the pseudo spectrum.

    p_spectrum = numpy.zeros(181)
    return p_spectrum

if __name__ == "__main__":
    sample

    # build received signal matrix
    
    # call music

    pass