"""Signal detection and channelization.

Turns wideband multi-channel IQ into per-signal bearing estimates: FFT
channelize, estimate the noise floor, threshold-detect active signals, then
run MUSIC on the FFT bin of each detection so every station on the band gets
its own bearing.
"""
from dataclasses import dataclass

import numpy as np

from . import music


@dataclass(frozen=True)
class Detection:
    """An active signal found in the averaged power spectrum."""

    bin_index: int
    offset_hz: float
    power_db: float
    snr_db: float


@dataclass(frozen=True)
class SignalBearing:
    """A detected signal together with its estimated bearing."""

    freq_hz: float
    bearing_deg: float
    snr_db: float


def stft_frames(iq, nfft):
    """Non-overlapping FFT frames of an (M, N) IQ array.

    Returns an (M, num_frames, nfft) complex array; trailing samples that do
    not fill a whole frame are dropped. Frame f, bin b across the M channels
    is one MUSIC snapshot for the frequency of bin b.
    """
    iq = np.asarray(iq)
    num_channels, num_samples = iq.shape
    num_frames = num_samples // nfft
    if num_frames == 0:
        raise ValueError(f"need at least {nfft} samples, got {num_samples}")
    frames = iq[:, : num_frames * nfft].reshape(num_channels, num_frames, nfft)
    return np.fft.fft(frames, axis=2)


def average_power_db(frames):
    """Power spectrum in dB, averaged over channels and frames."""
    power = np.mean(np.abs(frames) ** 2, axis=(0, 1)) / frames.shape[2]
    return 10.0 * np.log10(power)


def noise_floor_db(psd_db):
    """Median-based noise floor estimate; robust to a few strong signals."""
    return float(np.median(psd_db))


def detect_signals(psd_db, sample_rate_hz, threshold_db=10.0):
    """Signals whose power exceeds the noise floor by ``threshold_db``.

    Adjacent above-threshold bins (including across the FFT wrap point) are
    grouped into one detection at the group's strongest bin. Returns a list
    of Detections sorted by descending power.
    """
    psd_db = np.asarray(psd_db)
    nfft = psd_db.size
    floor = noise_floor_db(psd_db)
    above = psd_db > floor + threshold_db

    detections = []
    for group in _circular_groups(above):
        best = group[np.argmax(psd_db[group])]
        offsets = np.fft.fftfreq(nfft, d=1.0 / sample_rate_hz)
        detections.append(
            Detection(
                bin_index=int(best),
                offset_hz=float(offsets[best]),
                power_db=float(psd_db[best]),
                snr_db=float(psd_db[best] - floor),
            )
        )
    return sorted(detections, key=lambda d: d.power_db, reverse=True)


def estimate_signal_bearings(
    iq,
    array,
    center_freq_hz,
    sample_rate_hz,
    nfft=1024,
    threshold_db=10.0,
):
    """Bearing of every detected signal in a wideband IQ capture.

    Channelizes the capture, detects active signals, and runs single-source
    MUSIC on each detection's FFT bin (one snapshot per frame). Returns a
    list of SignalBearings sorted by descending SNR.
    """
    frames = stft_frames(iq, nfft)
    detections = detect_signals(average_power_db(frames), sample_rate_hz, threshold_db)

    results = []
    for detection in detections:
        snapshots = frames[:, :, detection.bin_index]
        freq_hz = center_freq_hz + detection.offset_hz
        (bearing,) = music.estimate_bearings(snapshots, array, freq_hz, num_signals=1)
        results.append(
            SignalBearing(
                freq_hz=freq_hz,
                bearing_deg=float(bearing),
                snr_db=detection.snr_db,
            )
        )
    return results


def _circular_groups(mask):
    """Runs of consecutive True values, treating the array as circular."""
    mask = np.asarray(mask, dtype=bool)
    if mask.all():
        return [np.arange(mask.size)]
    indices = np.flatnonzero(mask)
    if indices.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(indices) > 1) + 1
    groups = np.split(indices, breaks)
    # Merge the first and last runs when the mask wraps around bin 0.
    if len(groups) > 1 and mask[0] and mask[-1]:
        groups[0] = np.concatenate([groups.pop(), groups[0]])
    return groups
