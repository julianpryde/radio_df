# radio_df
Direction finding of HF radio signals

RF processing system in the HAM frequency band that uses a 3 or 4 antenna array to find the rough direction of an incoming signal.

output is a dashboard with a time-bearing display of incoming radio signals. most recent signals are at the top, older signals are at the bottom of the waterfall.

See [PLAN.md](PLAN.md) for the project roadmap and recommended hardware.

## Usage

```sh
pip install -e .[display,dev]   # numpy core; pyqtgraph for the dashboard
python -m pytest                # run the test suite (no hardware needed)
python -m radio_df.display     # dashboard demo with simulated signals
python -m radio_df.display --polar   # same, as a polar disc
```

The pipeline lives in the `radio_df` package: `simulate` (synthetic IQ),
`music` (MUSIC bearing estimation on a circular array), `detect`
(channelization + per-signal bearings), `display` (waterfall/polar dashboard),
with `acquire` and `calibrate` stubs awaiting receiver hardware.