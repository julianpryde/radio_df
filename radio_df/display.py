"""Dashboard: time-bearing waterfall of detected signals.

The data model (BearingWaterfall) and the polar "rotating azimuth" disc
renderer (PolarDiscMap) are pure numpy and run headless; the interactive
pyqtgraph dashboard on top of them needs the ``display`` extra
(``pip install radio_df[display]``).

The polar renderer replaces the per-pixel loops of the old MLG-test.py
prototype: the disc-pixel -> (age row, bearing column) mapping is computed
once at construction and every frame is then a single numpy gather.

Run ``python -m radio_df.display`` for a demo fed with simulated bearings.
"""
import numpy as np


class BearingWaterfall:
    """Ring buffer of bearing observations: newest row on top.

    The image is (num_rows, 360): one column per degree of bearing, one row
    per update interval, newest at row 0 as the README describes.
    """

    NUM_BEARINGS = 360

    def __init__(self, num_rows):
        self._image = np.zeros((num_rows, self.NUM_BEARINGS))

    @property
    def image(self):
        return self._image

    def add_row(self, observations):
        """Scroll one interval and record (bearing_deg, intensity) pairs."""
        self._image[1:] = self._image[:-1]
        self._image[0] = 0.0
        for bearing_deg, intensity in observations:
            column = int(round(bearing_deg)) % self.NUM_BEARINGS
            self._image[0, column] = max(self._image[0, column], intensity)

    def add_signals(self, signals):
        """Record a list of detect.SignalBearing results as one row."""
        self.add_row((s.bearing_deg, s.snr_db) for s in signals)


class PolarDiscMap:
    """Renders a BearingWaterfall image onto a polar disc.

    Bearing 0 is up, 90 is right (compass convention). The newest data is
    drawn on the outer rim and scrolls toward the center, with the innermost
    ``1 - aspect`` fraction of the radius left empty — the same layout as the
    old prototype. The pixel -> (row, column) gather map is precomputed once.
    """

    def __init__(self, waterfall, diameter=500, aspect=0.4):
        num_rows = waterfall.image.shape[0]
        center = (diameter - 1) / 2.0
        rows_idx, cols_idx = np.indices((diameter, diameter))
        dx = cols_idx - center
        dy = center - rows_idx  # screen y grows downward
        radius = np.hypot(dx, dy)
        bearing_deg = np.degrees(np.arctan2(dx, dy)) % 360.0

        outer = diameter / 2.0
        inner = outer * (1.0 - aspect)
        self._valid = (radius <= outer) & (radius > inner)

        age = (outer - radius) / (outer - inner) * num_rows
        age_row = np.clip(age.astype(int), 0, num_rows - 1)

        self._age_row = age_row[self._valid]
        self._bearing_col = (
            bearing_deg[self._valid].round().astype(int) % BearingWaterfall.NUM_BEARINGS
        )
        self._shape = (diameter, diameter)

    def render(self, waterfall):
        """Gather the waterfall image onto the disc; O(pixels), no loops."""
        disc = np.zeros(self._shape)
        disc[self._valid] = waterfall.image[self._age_row, self._bearing_col]
        return disc


def _add_bearing_tickmarks(plot, diameter=500):
    """Add compass bearing labels and tickmarks around the polar disc perimeter."""
    try:
        import pyqtgraph as pg
    except ImportError:
        return

    # Bearing labels at cardinal and intercardinal directions
    bearings = [
        (0, "N"),
        (45, "NE"),
        (90, "E"),
        (135, "SE"),
        (180, "S"),
        (225, "SW"),
        (270, "W"),
        (315, "NW"),
    ]

    center = (diameter - 1) / 2.0
    radius = diameter / 2.0

    # Add tickmarks and labels around the circle
    for bearing_deg, label in bearings:
        # Convert bearing to radians (bearing 0° is up, so subtract from 90°)
        angle_rad = np.radians(90 - bearing_deg)

        # Position for tick mark (on the circle perimeter)
        tick_radius = radius * 0.98
        tick_x = center + tick_radius * np.cos(angle_rad)
        tick_y = center + tick_radius * np.sin(angle_rad)

        # Position for label (further out)
        label_radius = radius * 1.12
        label_x = center + label_radius * np.cos(angle_rad)
        label_y = center + label_radius * np.sin(angle_rad)

        # Add text label
        text = pg.TextItem(label, anchor=(0.5, 0.5), color=(200, 200, 200))
        text.setPos(label_x, label_y)
        plot.addItem(text)

        # Add tick mark (small line from 95% to 98% of radius)
        tick_inner = radius * 0.95
        tick_inner_x = center + tick_inner * np.cos(angle_rad)
        tick_inner_y = center + tick_inner * np.sin(angle_rad)

        line = pg.PlotCurveItem(
            x=[tick_inner_x, tick_x],
            y=[tick_inner_y, tick_y],
            pen=pg.mkPen(color=(200, 200, 200), width=2),
        )
        plot.addItem(line)


def run_dashboard(signal_source, num_rows=200, interval_ms=200, polar=False):
    """Show a live dashboard fed by an iterator of signal lists.

    ``signal_source`` yields, per update interval, a list of
    detect.SignalBearing (or (bearing_deg, intensity) tuples). Requires
    pyqtgraph and a Qt binding (``pip install radio_df[display]``).
    """
    try:
        import pyqtgraph as pg
        from pyqtgraph.Qt import QtCore
    except ImportError as error:
        raise ImportError(
            "the dashboard needs pyqtgraph and a Qt binding: "
            "pip install radio_df[display]"
        ) from error

    waterfall = BearingWaterfall(num_rows)
    disc_map = PolarDiscMap(waterfall) if polar else None

    app = pg.mkQApp("radio_df")
    window = pg.GraphicsLayoutWidget(title="radio_df — time-bearing waterfall")
    plot = window.addPlot()
    image_item = pg.ImageItem(axisOrder="row-major")
    plot.addItem(image_item)
    if polar:
        plot.hideAxis("bottom")
        plot.hideAxis("left")
        plot.setAspectLocked(True)
        _add_bearing_tickmarks(plot, diameter=disc_map._shape[0])
    else:
        plot.setLabel("bottom", "bearing", units="°")
        plot.setLabel("left", "age (newest at top)")
        plot.invertY(True)

    def update():
        try:
            signals = next(signal_source)
        except StopIteration:
            timer.stop()
            return
        if signals and hasattr(signals[0], "bearing_deg"):
            waterfall.add_signals(signals)
        else:
            waterfall.add_row(signals)
        image_item.setImage(
            disc_map.render(waterfall) if polar else waterfall.image,
            autoLevels=True,
        )

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(interval_ms)
    window.show()
    pg.exec()


def _demo_signal_source(rng=None):
    """Endless simulated observations: two drifting stations plus clutter."""
    rng = np.random.default_rng(rng)
    bearings = np.array([70.0, 250.0])
    while True:
        bearings = (bearings + rng.normal(0.0, 1.0, bearings.size)) % 360.0
        observations = [(b, 10.0 + rng.normal(0.0, 1.0)) for b in bearings]
        if rng.random() < 0.2:
            observations.append((rng.uniform(0.0, 360.0), rng.uniform(3.0, 8.0)))
        yield observations


if __name__ == "__main__":
    import sys

    run_dashboard(_demo_signal_source(), polar="--polar" in sys.argv)
