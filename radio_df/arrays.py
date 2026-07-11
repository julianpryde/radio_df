"""Antenna array geometries and their steering vectors."""
from dataclasses import dataclass

import numpy as np

SPEED_OF_LIGHT = 299_792_458.0


@dataclass(frozen=True)
class UniformCircularArray:
    """Antenna elements equally spaced on a circle.

    Element k sits at bearing 360*k/num_elements degrees (element 0 at 0
    degrees, i.e. "north"), all at ``radius_m`` from the array center. Unlike
    a linear array, this geometry resolves bearings over the full 360 degrees.
    """

    num_elements: int
    radius_m: float

    def element_bearings_rad(self):
        return 2.0 * np.pi * np.arange(self.num_elements) / self.num_elements

    def steering_vector(self, bearing_deg, freq_hz):
        """Phase response of each element to a plane wave from ``bearing_deg``.

        ``bearing_deg`` may be a scalar or an array; the result has shape
        (num_elements,) or (num_elements, len(bearing_deg)). Each column has
        unit-magnitude entries.
        """
        wavelength = SPEED_OF_LIGHT / freq_hz
        bearing_rad = np.atleast_1d(np.deg2rad(bearing_deg))
        # Path-length advance of an element toward the source, relative to
        # the array center: r * cos(bearing - element_bearing).
        delays = self.radius_m * np.cos(
            bearing_rad[np.newaxis, :] - self.element_bearings_rad()[:, np.newaxis]
        )
        vectors = np.exp(2j * np.pi * delays / wavelength)
        if np.isscalar(bearing_deg) or np.ndim(bearing_deg) == 0:
            return vectors[:, 0]
        return vectors
