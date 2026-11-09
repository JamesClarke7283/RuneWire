# RuneWire audio sources

Every sound effect and music loop in `assets/audio/` is synthesised from scratch by the Python
scripts in this folder. Nothing is sampled or downloaded. The scripts need numpy, so run them
with Blender's bundled Python from the project root:

```sh
env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_sfx.py    # 73 SFX, about 20 s
env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_music.py  # 3 loops, about 2 min
env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/qa.py          # previews + SOUNDS.md
```

You can rebuild only some files by passing their names after `--`:

- `make_sfx.py -- coin_pickup reward --nopreview` takes sound names or group names.
- `make_music.py -- town` takes `town`, `combat` or `menu`.

The output is deterministic. Each sound seeds its RNG from its own name, so a rebuild gives identical files.

| File | Contents |
|---|---|
| `synth.py` | The numpy DSP core. **Oscillators:** band-limited polyBLEP saw and square, additive, Chebyshev harmonic stacks with time-varying brightness, FM. **Noise:** white, pink and brown. **Filters:** zero-phase FFT filters, STFT time-varying sweeps, a TPT state-variable filter. **Synthesis:** modal resonators and Karplus-Strong strings. **Effects:** oversampled saturation, chorus, an exact FFT feedback delay, and a synthetic-IR convolution reverb. **Mastering and output:** K-weighted loudness, a true-peak look-ahead limiter, and a WAV writer that adds a `smpl` loop chunk. |
| `instruments.py` | Reusable layers. **Sound design:** thump, noise burst, crackle, whoosh, sparkle, metal/wood hits, zap, servo, formant voice. **Instruments:** bells (glock, celesta, coin, crystal, vibes, marimba), plucks (harp, pizzicato, bass), brass, strings, pads, and a legato flute/clarinet/horn line. **Drums:** kick, snare, hats, shaker, tambourine, woodblock, toms, taiko, timpani, crash, triangle. |
| `make_sfx.py` | One function per sound effect, plus loudness matching and writing. |
| `music.py`, `make_music.py` | A small circular sequencer (chords, voicing, phrases, mixdown, mastering) and the three compositions. |
| `qa.py` | Reads the WAVs back and writes waveform/spectrogram/seam contact sheets to `art/previews/audio/`. It also writes `SOUNDS.md`, the per-file manifest. |

## Output conventions

- **SFX:** `assets/audio/sfx/<name>.wav`, 16-bit PCM, 44.1 kHz, mono.
- **Music:** `assets/audio/music/<name>.wav`, 16-bit PCM, 44.1 kHz, stereo, 68–80 s loops.
- **Peaks:** the true peak is at or below −1 dBTP everywhere.
- **One-shot loudness:** one-shots are loudness-matched per group: ui, reward, step, spell, weapon and so on (see `TARGETS` in `make_sfx.py`). They are then limited by at most 4 dB. Most one-shots peak between −1 and −2 dBFS. Sustained tonal sounds such as `tool_configure`, `notify` and `ui_error` peak lower, because matching their loudness would otherwise make them much louder than their group.
- **Loop loudness:** loops use integrated loudness. Contraption loops sit at −16 LUFS, enemy idle loops at −17 LUFS and ambience beds at −20 LUFS.
- **Music loudness:** town is −16 LUFS, combat −15 and menu −18.
- **One-shot edges:** one-shots start and end on silence, with 1.5 ms and up to 30 ms raised-cosine fades.

## Loops

`*_loop` SFX and all music are rendered into a circular buffer exactly one loop long:

- every oscillator runs a whole number of cycles;
- filters, chorus, delays and reverb wrap around;
- note and reverb tails continue past the loop point into the start.

So the seam is just another sample, and the QA seam test shows it behaves like any interior point.

Each looping file also carries a RIFF `smpl` chunk with one forward loop from 0 to the frame count. Godot's WAV importer default, `edit/loop_mode = Detect From WAV`, reads that chunk, so these streams loop with no import tweaks. If someone changes the import mode, use `Forward` with `loop_begin = 0` and `loop_end = -1`.
