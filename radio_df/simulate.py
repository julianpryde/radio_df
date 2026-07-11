"""Synthetic IQ generation for testing the pipeline without hardware.

Given an array geometry, source bearings, and an SNR, produce the
multi-channel received-signal matrix that the receiver would deliver. This is
the test oracle for the MUSIC implementation, signal detection, and display.
"""
import numpy as np


def simulate_snapshots(
    array,
    bearings_deg,
    freq_hz,
    num_snapshots,
    snr_db=20.0,
    rng=None,
):
    """Narrowband received-signal matrix for sources at known bearings.

    Each source transmits unit-power circular complex Gaussian symbols; noise
    is added per element so that each source is ``snr_db`` above the
    per-element noise power. Returns X with shape
    (array.num_elements, num_snapshots).
    """
    rng = np.random.default_rng(rng)
    bearings_deg = np.atleast_1d(np.asarray(bearings_deg, dtype=float))

    steering = array.steering_vector(bearings_deg, freq_hz)
    symbols = _complex_gaussian(rng, (bearings_deg.size, num_snapshots))

    noise_power = 10.0 ** (-snr_db / 10.0)
    noise = np.sqrt(noise_power) * _complex_gaussian(
        rng, (array.num_elements, num_snapshots)
    )
    return steering @ symbols + noise


def _complex_gaussian(rng, shape):
    """Unit-power circular complex Gaussian samples."""
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2.0)
