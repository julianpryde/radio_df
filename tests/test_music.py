import numpy as np
import pytest

from radio_df import music
from radio_df.arrays import UniformCircularArray
from radio_df.simulate import simulate_snapshots

FREQ_HZ = 7.1e6
ARRAY = UniformCircularArray(num_elements=4, radius_m=3.0)


def bearing_error_deg(estimate, truth):
    return abs((estimate - truth + 180.0) % 360.0 - 180.0)


def test_covariance_matrix_shape_and_hermitian():
    x = simulate_snapshots(ARRAY, 10.0, FREQ_HZ, 128, rng=0)
    r = music.covariance_matrix(x)
    assert r.shape == (4, 4)
    np.testing.assert_allclose(r, r.conj().T)


def test_noise_subspace_rejects_bad_num_signals():
    r = np.eye(4, dtype=complex)
    with pytest.raises(ValueError):
        music.noise_subspace(r, 0)
    with pytest.raises(ValueError):
        music.noise_subspace(r, 4)


def test_noise_subspace_orthogonal_to_steering():
    bearing = 250.0
    x = simulate_snapshots(ARRAY, bearing, FREQ_HZ, 5000, snr_db=30.0, rng=1)
    noise = music.noise_subspace(music.covariance_matrix(x), num_signals=1)
    steering = ARRAY.steering_vector(bearing, FREQ_HZ)
    leakage = np.linalg.norm(noise.conj().T @ steering) / np.linalg.norm(steering)
    assert leakage < 0.05


@pytest.mark.parametrize("true_bearing", [0.0, 77.0, 145.0, 233.0, 359.0])
def test_single_source_bearing_within_2_degrees(true_bearing):
    x = simulate_snapshots(ARRAY, true_bearing, FREQ_HZ, 400, snr_db=15.0, rng=3)
    (estimate,) = music.estimate_bearings(x, ARRAY, FREQ_HZ, num_signals=1)
    assert bearing_error_deg(estimate, true_bearing) <= 2.0


def test_two_sources_separated():
    truths = [60.0, 195.0]
    x = simulate_snapshots(ARRAY, truths, FREQ_HZ, 1000, snr_db=20.0, rng=4)
    estimates = music.estimate_bearings(x, ARRAY, FREQ_HZ, num_signals=2)
    assert len(estimates) == 2
    for truth in truths:
        assert min(bearing_error_deg(e, truth) for e in estimates) <= 3.0


def test_three_element_array():
    array3 = UniformCircularArray(num_elements=3, radius_m=3.0)
    true_bearing = 300.0
    x = simulate_snapshots(array3, true_bearing, FREQ_HZ, 400, snr_db=15.0, rng=5)
    (estimate,) = music.estimate_bearings(x, array3, FREQ_HZ, num_signals=1)
    assert bearing_error_deg(estimate, true_bearing) <= 2.0


def test_pseudo_spectrum_peak_at_source():
    true_bearing = 123.0
    x = simulate_snapshots(ARRAY, true_bearing, FREQ_HZ, 400, snr_db=20.0, rng=6)
    spectrum = music.pseudo_spectrum(x, ARRAY, FREQ_HZ, num_signals=1)
    assert spectrum.shape == (360,)
    assert bearing_error_deg(float(np.argmax(spectrum)), true_bearing) <= 2.0
