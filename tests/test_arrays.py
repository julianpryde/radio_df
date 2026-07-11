import numpy as np

from radio_df.arrays import SPEED_OF_LIGHT, UniformCircularArray

FREQ_HZ = 7.1e6  # 40 m ham band
ARRAY = UniformCircularArray(num_elements=4, radius_m=3.0)


def test_steering_vector_unit_magnitude():
    vector = ARRAY.steering_vector(123.0, FREQ_HZ)
    assert vector.shape == (4,)
    np.testing.assert_allclose(np.abs(vector), 1.0)


def test_steering_vector_vectorized_matches_scalar():
    bearings = np.array([0.0, 45.0, 210.0])
    matrix = ARRAY.steering_vector(bearings, FREQ_HZ)
    assert matrix.shape == (4, 3)
    for column, bearing in zip(matrix.T, bearings):
        np.testing.assert_allclose(column, ARRAY.steering_vector(bearing, FREQ_HZ))


def test_steering_vector_geometry():
    # A wave from bearing 0 reaches element 0 (at bearing 0) early by
    # radius/c and the opposite element late by the same amount.
    wavelength = SPEED_OF_LIGHT / FREQ_HZ
    vector = ARRAY.steering_vector(0.0, FREQ_HZ)
    expected_phase = 2.0 * np.pi * ARRAY.radius_m / wavelength
    np.testing.assert_allclose(np.angle(vector[0]), expected_phase, atol=1e-9)
    np.testing.assert_allclose(np.angle(vector[2]), -expected_phase, atol=1e-9)
    # The two broadside elements see zero relative delay.
    np.testing.assert_allclose(np.angle(vector[1]), 0.0, atol=1e-9)
    np.testing.assert_allclose(np.angle(vector[3]), 0.0, atol=1e-9)


def test_distinct_bearings_have_distinct_steering():
    a = ARRAY.steering_vector(10.0, FREQ_HZ)
    b = ARRAY.steering_vector(200.0, FREQ_HZ)
    correlation = np.abs(np.vdot(a, b)) / ARRAY.num_elements
    assert correlation < 0.99
