"""MUSIC (MUltiple SIgnal Classification) angle-of-arrival estimation.

Takes the multi-channel received-signal matrix from a phase-coherent array
and estimates the bearings of the incoming signals. Requires a pre-defined
number of expected signals D. Only works for one frequency at a time, so D
usually = 1; D would only be > 1 for multiple arrival paths of the same
signal or two stations transmitting on the same frequency.

Step outline adapted from the Princeton COS463 lab, but with a uniform
circular array steering model (full 360-degree coverage) instead of the
lab's linear array (which only resolves -90..+90 degrees):
https://www.cs.princeton.edu/courses/archive/spring18/cos463/labs/lab5_preview.html
"""
import numpy as np

DEFAULT_BEARING_GRID_DEG = np.arange(360.0)


def covariance_matrix(received_signal):
    """Sample covariance R = X X^H / K of an (M, K) snapshot matrix."""
    received_signal = np.asarray(received_signal)
    num_snapshots = received_signal.shape[1]
    return received_signal @ received_signal.conj().T / num_snapshots


def noise_subspace(covariance, num_signals):
    """Eigenvectors of the M-D smallest eigenvalues, as an (M, M-D) matrix.

    eigh returns eigenvalues in ascending order, so the noise subspace is
    the first M-D columns.
    """
    num_elements = covariance.shape[0]
    if not 0 < num_signals < num_elements:
        raise ValueError(
            f"num_signals must be between 1 and {num_elements - 1}, "
            f"got {num_signals}"
        )
    _, eigenvectors = np.linalg.eigh(covariance)
    return eigenvectors[:, : num_elements - num_signals]


def pseudo_spectrum(
    received_signal,
    array,
    freq_hz,
    num_signals=1,
    bearing_grid_deg=DEFAULT_BEARING_GRID_DEG,
):
    """MUSIC pseudo-spectrum P(theta) = 1 / ||E_n^H a(theta)||^2.

    Peaks appear at the bearings of incoming signals. Returns an array the
    same length as ``bearing_grid_deg``.
    """
    covariance = covariance_matrix(received_signal)
    noise = noise_subspace(covariance, num_signals)
    steering = array.steering_vector(bearing_grid_deg, freq_hz)
    projections = noise.conj().T @ steering
    return 1.0 / np.sum(np.abs(projections) ** 2, axis=0)


def find_peaks_circular(spectrum, num_peaks):
    """Indices of the ``num_peaks`` largest local maxima on a circular grid."""
    spectrum = np.asarray(spectrum)
    is_peak = (spectrum > np.roll(spectrum, 1)) & (spectrum >= np.roll(spectrum, -1))
    peak_indices = np.flatnonzero(is_peak)
    if peak_indices.size == 0:
        peak_indices = np.array([int(np.argmax(spectrum))])
    ranked = peak_indices[np.argsort(spectrum[peak_indices])[::-1]]
    return ranked[:num_peaks]


def estimate_bearings(
    received_signal,
    array,
    freq_hz,
    num_signals=1,
    bearing_grid_deg=DEFAULT_BEARING_GRID_DEG,
):
    """Bearings (degrees) of the ``num_signals`` strongest pseudo-spectrum peaks.

    Returned sorted ascending. May return fewer than ``num_signals`` bearings
    when sources are too close together to resolve.
    """
    spectrum = pseudo_spectrum(
        received_signal, array, freq_hz, num_signals, bearing_grid_deg
    )
    peaks = find_peaks_circular(spectrum, num_signals)
    return np.sort(np.asarray(bearing_grid_deg)[peaks])
