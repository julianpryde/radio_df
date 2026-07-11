# radio_df
Direction finding of HF radio signals

RF processing system in the HAM frequency band that uses a 3 or 4 antenna array to find the rough direction of an incoming signal.

output is a dashboard with a time-bearing display of incoming radio signals. most recent signals are at the top, older signals are at the bottom of the waterfall.

See [PLAN.md](PLAN.md) for the project roadmap and recommended hardware.

## Installation & Usage

### Linux / macOS (bash, zsh)

```sh
# Install with display and dev extras (note the single quotes to prevent shell glob expansion)
pip install -e '.[display,dev]'

# Run tests (no hardware needed)
python -m pytest

# Run the dashboard demo
python -m radio_df.display         # time-bearing waterfall
python -m radio_df.display --polar # rotating azimuth disc
```

### Windows (PowerShell or cmd)

```cmd
REM PowerShell or cmd — square brackets don't need escaping
pip install -e ".[display,dev]"

python -m pytest
python -m radio_df.display
python -m radio_df.display --polar
```

The pipeline lives in the `radio_df` package: `simulate` (synthetic IQ),
`music` (MUSIC bearing estimation on a circular array), `detect`
(channelization + per-signal bearings), `display` (waterfall/polar dashboard),
with `acquire` and `calibrate` stubs awaiting receiver hardware.