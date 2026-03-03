# Real-Time MIDI Motif Generator

A live MIDI generation system for creating evolving house and EDM melodic patterns with harmonic awareness, optional chord progressions, and bass lines. Designed for real-time recording into your DAW.

## Features

- **15 Style Presets** - From deep house grooves to festival anthems
- **Real-Time Multi-Channel Output** - Lead melodies, chord progressions, and bass lines
- **Harmonic Intelligence** - Melodies automatically follow chord changes
- **Motif Memory System** - Recalls and transforms phrases for musical continuity
- **5 Scale Modes** - Major, minor, dorian, mixolydian, harmonic minor
- **Swing Timing** - Adjustable groove feel per preset
- **Monophonic Lead Engine** - No overlapping notes for mono synths

## Installation

### Prerequisites

- Python 3.7+
- A DAW (Reaper, Ableton Live, FL Studio, Logic Pro, etc.)
- Virtual MIDI driver:
  - **Windows**: loopMIDI
  - **macOS**: Built-in IAC Driver
  - **Linux**: ALSA or JACK

### Python Dependencies

```bash
pip install mido python-rtmidi
```

### Windows: Setting Up loopMIDI

loopMIDI creates virtual MIDI cables between the Python script and your DAW.

#### Step 1: Download and Install

1. Visit: https://www.tobias-erichsen.de/software/loopmidi.html
2. Download the installer
3. Run the installer (no configuration needed during install)

#### Step 2: Create Virtual MIDI Ports

1. **Launch loopMIDI** (should be in your Start Menu)
2. You'll see a window with a list of virtual ports
3. Click the **+** button at the bottom
4. A new port appears with a default name
5. **Rename it to exactly:** `GENMIDI 1 1`
   - Double-click the port name to edit
   - Type `GENMIDI 1 1` (include the spaces)
   - Press Enter
6. The port should show as **"active"** with a green indicator

**Important:** The port name must match EXACTLY what's in the code. Any difference (extra spaces, different capitalization) will break the connection.

#### Step 3: Keep loopMIDI Running

- loopMIDI must remain open while using the script
- You can minimize it, but don't close it
- If the port disappears, just reopen loopMIDI and it will reappear

### macOS: Setting Up IAC Driver

1. Open **Audio MIDI Setup** (Applications > Utilities > Audio MIDI Setup)
2. Go to **Window > Show MIDI Studio**
3. Double-click the **IAC Driver** icon
4. Check **"Device is online"**
5. Note the port name (usually "IAC Driver Bus 1")
6. Update `MIDI_OUT_NAME` in the script to match:
   ```python
   MIDI_OUT_NAME = "IAC Driver Bus 1"
   ```

### Linux: ALSA/JACK Setup

Create a virtual MIDI port using `aconnect` or JACK, then update `MIDI_OUT_NAME` accordingly.

## Critical: Matching MIDI Port Names

**This is the #1 cause of "MIDI port not found" errors.**

The `MIDI_OUT_NAME` variable in the code **must exactly match** your virtual MIDI port:

```python
MIDI_OUT_NAME = "GENMIDI 1 1"  # Must match your loopMIDI port name EXACTLY
```

### Troubleshooting Port Names

If you get a "MIDI port not found" error:

1. Run the script once - it will show all available ports
2. Copy the **exact** port name from the error message
3. Update `MIDI_OUT_NAME` in the code
4. Save and run again

**Common mistakes:**
- Extra spaces: `"GENMIDI  1  1"` vs `"GENMIDI 1 1"`
- Wrong capitalization: `"genmidi 1 1"` vs `"GENMIDI 1 1"`
- Missing numbers: `"GENMIDI 1"` vs `"GENMIDI 1 1"`

## DAW Setup

### Creating Your MIDI Tracks

You'll need 1-3 MIDI tracks depending on whether you want just the lead or the full arrangement:

#### Option 1: Lead Only (Minimal Setup)

1. Create **1 MIDI track** in your DAW
2. Set MIDI input to: `GENMIDI 1 1`
3. Set MIDI channel to: **1** (Channel 0 in code = Channel 1 in DAW)
4. Load a synth (Vital, Serum, Diva, etc.)
5. Arm the track and enable monitoring

#### Option 2: Full Arrangement (Lead + Chords + Bass)

1. Create **3 MIDI tracks**:
   
   **Track 1 - Lead:**
   - MIDI input: `GENMIDI 1 1`
   - MIDI channel: **1**
   - Load a lead synth (Serum, Vital, Sylenth1)
   
   **Track 2 - Chords:**
   - MIDI input: `GENMIDI 1 1`
   - MIDI channel: **2**
   - Load a pad/chord synth (Pigments, Omnisphere, Diva)
   
   **Track 3 - Bass:**
   - MIDI input: `GENMIDI 1 1`
   - MIDI channel: **3**
   - Load a bass synth (SubLab, Massive, Serum)

2. **Arm all tracks** and **enable monitoring**
3. Set your project tempo to match the preset BPM (usually 122-130)

### Recommended Synth Settings

- **Lead**: Mono mode, short release, bright timbre
- **Chords**: Poly mode, reverb/delay, pad-like sound
- **Bass**: Mono mode, sub-heavy, tight envelope

## Usage

### Running the Generator

```bash
python motif_generator.py
```

### Interactive Setup Flow

The script will guide you through 4 choices:

#### 1. Choose Preset (1-15)

```
1. Deep House Groove
2. Festival Drop Lead
3. Ibiza Sunset
4. Berlin Dark
5. Progressive Anthem
6. Acid Pluck
7. Radio EDM Hook
8. Tech House Bounce
9. Pop House
10. Melodic Minor Drive
11. Future Rave
12. Uplifting Trancey
13. Groovy Organ House
14. Minimal Tech
15. Feel Good Summer
```

#### 2. Choose Output Mode

```
1. Motif only          - Just the lead melody (Channel 1)
2. Motif + Chords + Bass  - Full arrangement (Channels 1, 2, 3)
```

#### 3. Choose Scale Mode

```
1. major
2. minor
3. dorian
4. mixolydian
5. harmonic_minor
```

This overrides the preset's default scale.

#### 4. Choose Duration

```
Bars (8/16/32 or blank for infinite):
```

- **8 bars**: Quick test (16 seconds at 128 BPM)
- **16 bars**: Short loop (32 seconds)
- **32 bars**: Full section (64 seconds)
- **Blank**: Runs forever until you press Ctrl+C

### The Pre-Roll Countdown

After making your selections:

```
Pre-roll: 10 seconds. Arm tracks + press Record.
Starting in 10...
Starting in 9...
...
Starting in 1...
GO!
```

**What to do during the countdown:**
1. Verify all MIDI tracks are armed
2. Check monitoring is enabled
3. **Press RECORD in your DAW** (around 5-3 seconds)
4. The script starts playing at "GO!"

### Recording Workflow

1. **Run the script** → Make your selections
2. **Arm tracks** in your DAW during countdown
3. **Hit Record** when countdown reaches ~5 seconds
4. Script generates and plays MIDI in real-time
5. **Stop** when done (or let it finish if you set a bar count)
6. Edit the recorded MIDI as needed

### Stopping Playback

- **Press `Ctrl+C`** to stop gracefully
- All active notes will receive note-off messages (no stuck notes)

## Style Presets Explained

Each preset has unique characteristics:

| Preset | BPM | Scale | Swing | Density | Character |
|--------|-----|-------|-------|---------|-----------|
| **Deep House Groove** | 122 | Dorian | 15% | Medium | Warm, jazzy, laid-back |
| **Festival Drop Lead** | 128 | Minor | 5% | High | Energetic, anthem drops |
| **Ibiza Sunset** | 124 | Major | 10% | Medium | Uplifting, emotional |
| **Berlin Dark** | 124 | Minor | 20% | Low | Minimal, hypnotic, techno |
| **Progressive Anthem** | 128 | Mixolydian | 5% | Medium | Big room, epic buildups |
| **Acid Pluck** | 126 | Harmonic Minor | 25% | High | Squelchy, angular, 303-style |
| **Radio EDM Hook** | 128 | Major | 5% | Low | Catchy, pop-friendly |
| **Tech House Bounce** | 125 | Dorian | 30% | High | Groovy, percussive feel |
| **Pop House** | 124 | Major | 5% | Low | Simple, vocal-friendly |
| **Melodic Minor Drive** | 126 | Harmonic Minor | 15% | Medium | Driving, tension-filled |
| **Future Rave** | 128 | Minor | 5% | High | Modern, aggressive |
| **Uplifting Trancey** | 130 | Major | 0% | Medium | Straight, euphoric |
| **Groovy Organ House** | 123 | Dorian | 25% | High | Old-school, funky |
| **Minimal Tech** | 125 | Minor | 35% | Low | Sparse, hypnotic |
| **Feel Good Summer** | 122 | Major | 10% | Medium | Bright, happy vibes |

### Swing Explained

- **0% swing**: Straight, robotic timing (trance, future rave)
- **5-15% swing**: Subtle humanization (most house styles)
- **20-30% swing**: Noticeable groove (deep house, tech house)
- **35% swing**: Heavy shuffle feel (minimal tech)

## How It Works

### Harmonic Intelligence

The generator uses a **4-chord progression** that loops forever:

**Minor mode example:** i → VI → III → VII (e.g., Dm → Bb → F → C)

For each phrase (2 bars), the generator:
1. Determines chord roots for bar 1 and bar 2
2. Generates or recalls a motif
3. **Snaps notes to fit the chords:**
   - First and last note in each bar → chord tones
   - Strong beats (1 & 3) → chord tones
   - Weak beats → any scale tone

This creates melodies that sound "in key" and follow the harmony.

### Memory & Evolution

The **Motif Memory** system creates musical continuity:

1. **New motifs** are generated with stepwise melodic movement
2. **Stored in memory** after first use
3. **Reused with transformations**:
   - **Transpose**: Shift the melody up/down
   - **Rhythm Nudge**: Move note timings slightly
   - **Ornament**: Add quick approach notes
4. **Probability-based recall**: More-used motifs are more likely to return

This creates evolving patterns that feel human and intentional, not random.

### Monophonic Lead Generation

The lead channel uses `make_monophonic()` to prevent overlapping notes:

- If note B starts before note A ends, note A is shortened
- Perfect for mono synths (Moog, SH-101, TB-303)
- Minimum note duration: 0.1 beats (very short, percussive possible)

Chords and bass use standard polyphonic timing.

## Customization

### Changing the Musical Key

Edit line 28 in the code:

```python
DEFAULT_TONIC_MIDI = 62  # D4 (default)
```

**Common keys:**
- C4 = 60
- D4 = 62 (default)
- E4 = 64
- F4 = 65
- G4 = 67
- A4 = 69

### Changing Chord Progressions

Edit the `_select_loop()` method in `ProgressionEngine` (lines 183-197):

```python
def _select_loop(self, mode: str) -> List[int]:
    if mode == "minor":
        return [0, 5, 2, 6]  # i - VI - III - VII
    # Change to your preferred progression (scale degrees 0-6)
```

**Example progressions:**
- Major: `[0, 4, 5, 3]` = I-V-vi-IV (pop progression)
- Minor: `[0, 6, 5, 0]` = i-VII-VI-i (darker loop)
- Dorian: `[0, 3, 6, 0]` = i-IV-VII-i (modal jam)

### Creating Custom Presets

Copy an existing preset and modify:

```python
"My Custom Preset": StyleParams(
    "My Custom Preset",
    bpm=126,
    scale_mode="dorian",
    swing=0.20,              # 20% swing
    min_notes=4,             # Minimum notes per bar
    max_notes=7,             # Maximum notes per bar
    step_bias=0.7,           # 70% chance to move by step (vs. leap)
    reuse_prob=0.65,         # 65% chance to reuse motif vs. new
    recent_block_phrases=2,  # Don't reuse motifs from last 2 phrases
    w_transpose=0.45,        # Transformation weights (will be normalized)
    w_rhythm_nudge=0.35,
    w_ornament=0.20,
    snap_strong_beats=True,  # Snap beat 1 & 3 to chord tones
    snap_bar_edges=True      # Snap first/last note to chord tones
),
```

Add it to the `STYLE_PRESETS` dictionary (lines 63-89).

## Tips for Best Results

### Synth Selection

- **Lead**: Use mono synths or mono mode. Examples: Serum (mono), Vital (mono), Diva (mono mode)
- **Chords**: Pads work great. Try Omnisphere, Pigments, or Analog Lab presets
- **Bass**: Sub-focused sounds. SubLab, Serum bass presets, or Massive

### Effects

- **Lead**: Reverb + delay + slight distortion
- **Chords**: Long reverb, chorus, compress heavily
- **Bass**: Light saturation, sidechain to kick

### Recording Multiple Takes

1. Record lead only first (option 1)
2. Run again with chords + bass (option 2) on new tracks
3. Layer multiple lead takes with different presets
4. Edit and comp the best parts

### Editing Recorded MIDI

The recorded MIDI is editable:
- Quantize if needed (though swing timing is intentional)
- Adjust velocities for dynamics
- Move notes to fit your track better
- Copy/paste sections as loops

## Troubleshooting

### "MIDI port not found"

**Solution:**
1. Check loopMIDI is running (Windows) or IAC Driver is enabled (macOS)
2. Verify the port name matches EXACTLY
3. Run the script to see available ports
4. Update `MIDI_OUT_NAME` with the correct name

### No sound in DAW

**Checklist:**
- ✅ MIDI tracks are armed
- ✅ Monitoring is enabled (yellow/red light)
- ✅ MIDI channel matches (Lead = CH 1, Chords = CH 2, Bass = CH 3)
- ✅ Synths are loaded and producing sound
- ✅ MIDI input is set to `GENMIDI 1 1`
- ✅ Volume faders are up

### Stuck/Hanging Notes

**Solution:**
- Press `Ctrl+C` in the terminal (sends all-notes-off)
- Or send MIDI CC#123 (all notes off) in your DAW
- Check your DAW's panic button

### Timing/Latency Issues

**Solutions:**
- Close CPU-heavy applications
- Increase your DAW's audio buffer size (256 or 512 samples)
- Reduce the number of active plugins
- Use the 10-second pre-roll to get ready

### Chords/Bass Not Playing

**Check:**
- You selected option 2 (Motif + Chords + Bass) when prompted
- You have tracks set to MIDI channels 2 and 3
- Those tracks are armed and monitoring

## Technical Details

### Phrase Structure

- **1 beat** = quarter note
- **4 beats** = 1 bar
- **2 bars** = 1 phrase (8 beats)
- The generator works in 2-bar phrases
- Chord changes happen every bar

### MIDI Channels

- **Channel 0 (DAW Channel 1)**: Lead melody (monophonic)
- **Channel 1 (DAW Channel 2)**: Chord triads (polyphonic, 3 notes)
- **Channel 2 (DAW Channel 3)**: Bass root notes (monophonic)

### Scale Degrees

All melodies use scale degrees (0-6) internally:
- **0** = root (tonic)
- **2** = third
- **4** = fifth
- **6** = seventh

Chord tones = root (0), third (2), fifth (4)

## Requirements

- Python 3.7 or higher
- `mido` library
- `python-rtmidi` library
- loopMIDI (Windows) or IAC Driver (macOS)
- A DAW with MIDI input support

## Contributors

This project was developed by:

- **Hemanth**
- **Lydia**
- **Polyxeni**

## License

This project is licensed under the MIT License.
```
MIT License

Copyright (c) 2025 [Your Name/Team Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**Happy creating! 🎹🎶**
