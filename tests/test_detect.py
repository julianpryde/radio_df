import numpy as np

from radio_df import detect
from radio_df.arrays import UniformCircularArray
from radio_df.simulate import SimulatedSource, simulate_iq

CENTER_FREQ_HZ = 7.1e6
SAMPLE_RATE_HZ = 48_000.0
NFFT = 1024
ARRAY = UniformCircularArray(num_elements=4, radius_m=3.0)


def bin_centered_offset(bin_index):
    return bin_index * SAMPLE_RATE_HZ / NFFT


def bearing_error_deg(estimate, truth):
    return abs((estimate - truth + 180.0) % 360.0 - 180.0)


def make_capture(sources, num_frames=64, rng=0):
    return simulate_iq(
        ARRAY,
        sources,
        CENTER_FREQ_HZ,
        SAMPLE_RATE_HZ,
        num_samples=NFFT * num_frames,
        rng=rng,
    )


def test_stft_frames_shape_and_remainder():
    iq = make_capture([], num_frames=8)
    frames = detect.stft_frames(iq[:, :-100], NFFT)
    assert frames.shape == (4, 7, NFFT)


def test_no_detections_in_noise():
    iq = make_capture([], num_frames=32)
    psd_db = detect.average_power_db(detect.stft_frames(iq, NFFT))
    assert detect.detect_signals(psd_db, SAMPLE_RATE_HZ) == []


def test_detects_two_tones_at_correct_offsets():
    sources = [
        SimulatedSource(bearing_deg=40.0, offset_hz=bin_centered_offset(100), snr_db=10.0),
        SimulatedSource(bearing_deg=290.0, offset_hz=bin_centered_offset(-150), snr_db=5.0),
    ]
    iq = make_capture(sources)
    psd_db = detect.average_power_db(detect.stft_frames(iq, NFFT))
    detections = detect.detect_signals(psd_db, SAMPLE_RATE_HZ)
    assert len(detections) == 2
    found_offsets = sorted(d.offset_hz for d in detections)
    expected = sorted(s.offset_hz for s in sources)
    bin_width = SAMPLE_RATE_HZ / NFFT
    for found, want in zip(found_offsets, expected):
        assert abs(found - want) <= bin_width
    # Stronger tone should be reported first and with higher SNR.
    assert detections[0].snr_db > detections[1].snr_db


def test_bearings_per_detected_signal():
    sources = [
        SimulatedSource(bearing_deg=40.0, offset_hz=bin_centered_offset(100), snr_db=10.0),
        SimulatedSource(bearing_deg=290.0, offset_hz=bin_centered_offset(-150), snr_db=8.0),
    ]
    iq = make_capture(sources, rng=1)
    results = detect.estimate_signal_bearings(
        iq, ARRAY, CENTER_FREQ_HZ, SAMPLE_RATE_HZ, nfft=NFFT
    )
    assert len(results) == 2
    by_freq = {round(r.freq_hz - CENTER_FREQ_HZ): r for r in results}
    for source in sources:
        result = by_freq[round(source.offset_hz)]
        assert bearing_error_deg(result.bearing_deg, source.bearing_deg) <= 3.0


def test_circular_groups_wraparound():
    mask = np.zeros(16, dtype=bool)
    mask[[15, 0, 1, 7, 8]] = True
    groups = detect._circular_groups(mask)
    as_sets = sorted((frozenset(g.tolist()) for g in groups), key=min)
    assert as_sets == [frozenset({0, 1, 15}), frozenset({7, 8})]
