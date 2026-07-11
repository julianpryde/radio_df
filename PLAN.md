# Project Completion Plan

Goal (from README): direction finding of HF radio signals using a 3–4 element antenna
array, with a dashboard showing a time-bearing waterfall of incoming signals (newest at
the top).

## Where the project stands today

- `radio_df.py` — skeleton of the MUSIC (MUltiple SIgnal Classification) angle-of-arrival
  algorithm. Steps 1–5 are described in comments but not implemented. Known issues to fix
  when implementing:
  - `numpy.zeros(181)` should be `np.zeros(181)`.
  - Carrier frequency is hardcoded to 2.442 GHz (WiFi); it must be a parameter in the HF
    range (3–30 MHz).
  - The commented approach assumes a uniform *linear* array, which only resolves −90° to
    +90° and has front/back ambiguity. Full 360° coverage (what the README describes)
    needs a uniform *circular* array (UCA) steering model.
- `MLG-test.py` — tkinter prototype of a polar "rotating azimuth" (RAZ) disc display fed
  with random data. It works but is slow (triple-nested per-pixel Python loops), creates a
  new `tk.Label` every frame (memory leak), and the polar format differs from the
  rectangular time-bearing waterfall described in the README. The
  `pixel_position_transform()` stub already anticipates the right fix: precompute the
  polar→cartesian pixel mapping once and reuse it.

## Target architecture

```
4x HF antennas
  → 4-channel phase-coherent SDR receiver
  → IQ capture
  → calibration (per-channel phase/gain alignment via common noise source)
  → channelizer (FFT, per-bin signal detection)
  → MUSIC AoA estimation per detected signal (UCA steering vectors)
  → bearing/time/SNR records
  → dashboard (time-bearing waterfall, newest at top; polar disc as optional view)
```

## Phased milestones

### Phase 0 — Repo hygiene (~half a day)

Restructure into a package so each pipeline stage has a home:

```
radio_df/
  music.py       # AoA estimation (grows out of radio_df.py)
  simulate.py    # synthetic IQ generator
  calibrate.py   # phase/gain calibration
  acquire.py     # SDR interface
  display.py     # dashboard (grows out of MLG-test.py)
tests/
requirements.txt (or pyproject.toml)
```

Keep `MLG-test.py` as reference until the new display lands.

### Phase 1 — Simulation harness first (no hardware needed)

Build a synthetic IQ generator: given the array geometry, N sources at known bearings,
and an SNR, produce the M-channel received-signal matrix. This is the test oracle for
everything downstream — the MUSIC implementation, detection thresholds, and even the
display can be developed and validated before any hardware is purchased.

### Phase 2 — Implement MUSIC properly

Fill in steps 1–5 of `radio_df.py`:

1. Covariance matrix `R = X @ X.conj().T / K` (M×M for M antennas, K snapshots).
2. Eigendecomposition with `np.linalg.eigh(R)`.
3. Sort eigenvalues; the M−D smallest eigenvectors span the noise subspace (D = number
   of expected signals, usually 1).
4. Steering vectors for a **uniform circular array** of 3–4 elements, parameterized by
   frequency and array radius, so bearings resolve over the full 0–360°.
5. Sweep 0–360° in 1° steps, compute the pseudo-spectrum
   `P(θ) = 1 / (a(θ)ᴴ Eₙ Eₙᴴ a(θ))`, and peak-pick.

Unit tests against the Phase 1 simulator: bearing error under ~2° at moderate SNR,
correct separation of two sources.

### Phase 3 — Signal detection & channelization

FFT-based power spectrum per channel, noise-floor estimation, and threshold detection of
active signals. Run MUSIC on the bin(s) around each detection so multiple simultaneous
stations on different frequencies each get their own bearing. This is what turns "one
bearing at one frequency" into the multi-signal waterfall the README describes.

### Phase 4 — Display/dashboard rewrite

Replace the per-pixel tkinter loop with either:

- **Recommended:** a rectangular time-bearing waterfall (bearing on X, time on Y,
  color = signal strength) using `pyqtgraph` — fast, simple, and exactly matches the
  README description; or
- the existing polar RAZ disc, made fast by precomputing the polar-coordinate index map
  once (the `pixel_position_transform()` idea) and applying it with numpy fancy
  indexing — no Cython needed.

Keep the polar disc as an optional second view.

### Phase 5 — Hardware bring-up

- Acquisition driver reading coherent IQ from the chosen receiver (see hardware below).
- Phase/gain calibration: switch a common noise source, split 4 ways, into all inputs;
  measure and store a per-frequency correction table. Feedline lengths must be matched.
- End-to-end sanity test against a signal at a known bearing (WWV/CHU, a local AM
  broadcast station, or a cooperating local ham).

### Phase 6 — Integration & field validation

Real-time pipeline (acquire → calibrate → detect → MUSIC → display) with ring buffers.
Validate against stations of known location (WWV at 10/15 MHz, local nets) and document
the achieved bearing accuracy.

## Recommended hardware

The hard requirement is **phase-coherent multi-channel reception at 3–30 MHz**. Note that
the popular KrakenSDR tunes 24–1766 MHz, so it misses nearly all of HF — great for a
VHF/UHF warm-up and its open-source DF software is worth studying, but it is the wrong
receiver for this project.

| Tier | Receiver | ~Cost | Notes |
|---|---|---|---|
| **Recommended** | Afedri AFE822x dual-channel ×2 (clock-synced), or an Afedri 4-channel model | ~$500–900 | Native HF (0.1–35 MHz), coherent channels in one box, proven in amateur HF DF work |
| Alternative | 2× Red Pitaya STEMlab 125-14 with shared clock | ~$800 | 4× 14-bit 125 MSPS ADC channels, direct HF sampling, strong ham SDR ecosystem |
| Budget / experimental | 4× RTL-SDR v3 in direct-sampling mode with common-clock mod + noise-source calibration | ~$150 + labor | Cheapest coherent HF, but hacky: hardware mods, extra HF filtering, and careful calibration required |
| VHF/UHF warm-up only | KrakenSDR (5-channel coherent) | ~$500 | Turnkey coherent DF, open-source MUSIC software — but 24 MHz tuning floor |

Supporting hardware:

- **Antennas:** 4 identical **active whips (mini-whip)** or **active small loops**
  (e.g., LZ1AQ-style) arranged in a square (UCA). At HF, λ/2 element spacing is
  impractical (λ = 43 m at 7 MHz); MUSIC still works at ~0.1–0.2 λ spacing (a few
  meters) with reduced angular resolution. Identical antennas and matched-length
  feedlines are mandatory for phase accuracy.
- **Calibration:** wideband noise source + 4-way splitter + coax relay to switch it into
  all four inputs.
- **Clock:** a shared 10 MHz reference for all channels; a GPSDO (~$100–200) is optional
  but improves stability.
- **Compute:** any modern laptop or mini-PC during development; a Raspberry Pi 5 is
  feasible for a deployed unit.

## Suggested order of purchase

Nothing needs to be bought until Phase 5. Phases 0–4 run entirely against the simulator,
which also de-risks the hardware spend: by the time the receiver arrives, the whole
software chain is already tested.
