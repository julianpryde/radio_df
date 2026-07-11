import numpy as np

from radio_df.display import BearingWaterfall, PolarDiscMap


def test_waterfall_newest_on_top_and_scrolls():
    waterfall = BearingWaterfall(num_rows=3)
    waterfall.add_row([(10.0, 1.0)])
    waterfall.add_row([(20.0, 2.0)])
    assert waterfall.image[0, 20] == 2.0
    assert waterfall.image[1, 10] == 1.0
    waterfall.add_row([])
    waterfall.add_row([])
    # The first observation has scrolled off the bottom.
    assert np.count_nonzero(waterfall.image) == 1
    assert waterfall.image[2, 20] == 2.0


def test_waterfall_bearing_wraps():
    waterfall = BearingWaterfall(num_rows=2)
    waterfall.add_row([(359.6, 1.0), (-90.0, 2.0)])
    assert waterfall.image[0, 0] == 1.0
    assert waterfall.image[0, 270] == 2.0


def test_polar_map_compass_orientation():
    waterfall = BearingWaterfall(num_rows=10)
    waterfall.add_row([(0.0, 1.0), (90.0, 2.0)])
    disc = PolarDiscMap(waterfall, diameter=101, aspect=0.4).render(waterfall)
    center = 50
    # Newest data sits on the outer rim: bearing 0 is straight up from the
    # center, bearing 90 straight right.
    assert disc[1, center] == 1.0
    assert disc[center, 99] == 2.0
    # Nothing below (bearing 180) or left (bearing 270).
    assert disc[99, center] == 0.0
    assert disc[center, 1] == 0.0


def test_polar_map_age_moves_inward():
    waterfall = BearingWaterfall(num_rows=10)
    waterfall.add_row([(0.0, 1.0)])
    for _ in range(5):
        waterfall.add_row([])
    disc_map = PolarDiscMap(waterfall, diameter=101, aspect=0.4)
    disc = disc_map.render(waterfall)
    column = disc[:, 50]
    lit = np.flatnonzero(column == 1.0)
    assert lit.size > 0
    # Age 5 of 10 rows: roughly halfway into the annulus (rows 1..20 above
    # center for diameter 101, aspect 0.4).
    assert 5 <= lit[0] <= 15


def test_polar_map_center_and_outside_empty():
    waterfall = BearingWaterfall(num_rows=10)
    waterfall.add_row([(b, 1.0) for b in range(360)])
    disc = PolarDiscMap(waterfall, diameter=101, aspect=0.4).render(waterfall)
    assert disc[50, 50] == 0.0  # inner hole
    assert disc[0, 0] == 0.0  # corner outside the disc
