"""Synthetic IQ generation for testing the pipeline without hardware.

Given an array geometry, source bearings, and an SNR, produce the
multi-channel received-signal matrix that the receiver would deliver. This is
the test oracle for the MUSIC implementation, signal detection, and display.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulatedSource:
    """A transmitter for wideband IQ simulation.

    ``offset_hz`` is the carrier's offset from the receiver center frequency;
    ``snr_db`` is the tone's power relative to the full-band noise power.
    """

    bearing_deg: float
    offset_hz: float
    snr_db: float = 10.0


def simulate_iq(
    array,
    sources,
    center_freq_hz,
    sample_rate_hz,
    num_samples,
    rng=None,
):
    """Wideband multi-channel IQ with tones at several frequencies/bearings.

    Each ``SimulatedSource`` contributes a complex tone at its frequency
    offset, phased across the array according to its bearing at the actual RF
    frequency. Unit-power full-band noise is added per element. Returns an
    (array.num_elements, num_samples) complex array.
    """
    rng = np.random.default_rng(rng)
    times = np.arange(num_samples) / sample_rate_hz
    iq = _complex_gaussian(rng, (array.num_elements, num_samples))
    for source in sources:
        steering = array.steering_vector(
            source.bearing_deg, center_freq_hz + source.offset_hz
        )
        amplitude = 10.0 ** (source.snr_db / 20.0)
        phase = rng.uniform(0.0, 2.0 * np.pi)
        tone = amplitude * np.exp(
            1j * (2.0 * np.pi * source.offset_hz * times + phase)
        )
        iq += steering[:, np.newaxis] * tone[np.newaxis, :]
    return iq


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
