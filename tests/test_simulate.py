import numpy as np

from radio_df.arrays import UniformCircularArray
from radio_df.simulate import simulate_snapshots

FREQ_HZ = 7.1e6
ARRAY = UniformCircularArray(num_elements=4, radius_m=3.0)


def test_output_shape_and_dtype():
    x = simulate_snapshots(ARRAY, [30.0, 200.0], FREQ_HZ, num_snapshots=64, rng=0)
    assert x.shape == (4, 64)
    assert np.iscomplexobj(x)


def test_scalar_bearing_accepted():
    x = simulate_snapshots(ARRAY, 45.0, FREQ_HZ, num_snapshots=16, rng=0)
    assert x.shape == (4, 16)


def test_snr_controls_power():
    k = 20000
    quiet = simulate_snapshots(ARRAY, 90.0, FREQ_HZ, k, snr_db=0.0, rng=1)
    loud = simulate_snapshots(ARRAY, 90.0, FREQ_HZ, k, snr_db=20.0, rng=1)
    # Per-element power = signal (1.0) + noise (10^(-snr/10)).
    np.testing.assert_allclose(np.mean(np.abs(quiet) ** 2), 2.0, rtol=0.05)
    np.testing.assert_allclose(np.mean(np.abs(loud) ** 2), 1.01, rtol=0.05)


def test_covariance_dominated_by_steering_direction():
    bearing = 137.0
    x = simulate_snapshots(ARRAY, bearing, FREQ_HZ, 5000, snr_db=30.0, rng=2)
    covariance = x @ x.conj().T / x.shape[1]
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    principal = eigenvectors[:, -1]
    steering = ARRAY.steering_vector(bearing, FREQ_HZ)
    alignment = np.abs(np.vdot(principal, steering)) / (
        np.linalg.norm(principal) * np.linalg.norm(steering)
    )
    assert alignment > 0.99
