import time
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import mido

# ============================================================
# CONFIG
# ============================================================
MIDI_OUT_NAME = "GENMIDI 1 1"   # keep EXACT as your working output port name

BEATS_PER_BAR = 4
PHRASE_BARS = 2
PHRASE_BEATS = BEATS_PER_BAR * PHRASE_BARS

PREROLL_SECONDS = 10  # 10-second preroll

# Channels (0-based in MIDI)
CH_LEAD = 0
CH_CHORDS = 1
CH_BASS = 2

# ============================================================
# SCALES
# ============================================================
SCALES = {
    "major":          [0, 2, 4, 5, 7, 9, 11],
    "minor":          [0, 2, 3, 5, 7, 8, 10],
    "dorian":         [0, 2, 3, 5, 7, 9, 10],
    "mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
}

DEFAULT_TONIC_MIDI = 62  # D4


class ScaleEngine:
    def __init__(self, tonic: int, mode: str):
        self.tonic = tonic
        self.mode = mode

    def degree_to_midi(self, deg: int, octave: int = 0) -> int:
        return self.tonic + SCALES[self.mode][deg % 7] + 12 * octave


# ============================================================
# STYLE / PRESETS
# ============================================================
@dataclass
class StyleParams:
    name: str
    bpm: int
    scale_mode: str = "minor"
    tonic_midi: int = DEFAULT_TONIC_MIDI

    # lead generation
    min_notes: int = 4
    max_notes: int = 7
    step_bias: float = 0.7
    swing: float = 0.0  # 0..0.6 typical

    # motif memory
    reuse_prob: float = 0.65          # chance to reuse a motif instead of generating new
    recent_block_phrases: int = 2     # don't reuse motifs used too recently

    # transformations (relative weights)
    w_transpose: float = 0.45
    w_rhythm_nudge: float = 0.35
    w_ornament: float = 0.20

    # chord snapping strength
    snap_strong_beats: bool = True    # snap beat 1/3 to chord tones
    snap_bar_edges: bool = True       # snap first/last note in each bar to chord tones


STYLE_PRESETS = {
    "Deep House Groove": StyleParams("Deep House Groove", 122, "dorian", swing=0.15, reuse_prob=0.70),
    "Festival Drop Lead": StyleParams("Festival Drop Lead", 128, "minor", swing=0.05, reuse_prob=0.55, max_notes=8),
    "Ibiza Sunset": StyleParams("Ibiza Sunset", 124, "major", swing=0.10, reuse_prob=0.65),
    "Berlin Dark": StyleParams("Berlin Dark", 124, "minor", swing=0.20, reuse_prob=0.75, min_notes=3, max_notes=6),
    "Progressive Anthem": StyleParams("Progressive Anthem", 128, "mixolydian", swing=0.05, reuse_prob=0.60),
    "Acid Pluck": StyleParams("Acid Pluck", 126, "harmonic_minor", swing=0.25, reuse_prob=0.55, max_notes=8),
    "Radio EDM Hook": StyleParams("Radio EDM Hook", 128, "major", swing=0.05, reuse_prob=0.70, min_notes=3, max_notes=6),
    "Tech House Bounce": StyleParams("Tech House Bounce", 125, "dorian", swing=0.30, reuse_prob=0.75, max_notes=8),
    "Pop House": StyleParams("Pop House", 124, "major", swing=0.05, reuse_prob=0.70, min_notes=3, max_notes=6),
    "Melodic Minor Drive": StyleParams("Melodic Minor Drive", 126, "harmonic_minor", swing=0.15, reuse_prob=0.65),
    "Future Rave": StyleParams("Future Rave", 128, "minor", swing=0.05, reuse_prob=0.55, max_notes=8),
    "Uplifting Trancey": StyleParams("Uplifting Trancey", 130, "major", swing=0.00, reuse_prob=0.60),
    "Groovy Organ House": StyleParams("Groovy Organ House", 123, "dorian", swing=0.25, reuse_prob=0.75),
    "Minimal Tech": StyleParams("Minimal Tech", 125, "minor", swing=0.35, reuse_prob=0.80, min_notes=3, max_notes=6),
    "Feel Good Summer": StyleParams("Feel Good Summer", 122, "major", swing=0.10, reuse_prob=0.70),
}

# ============================================================
# NOTE MODELS
# ============================================================
class NoteEv:
    def __init__(self, start: float, dur: float, deg: int, vel: int):
        self.start = start
        self.dur = dur
        self.deg = deg
        self.vel = vel


class Motif:
    def __init__(self, notes: List[NoteEv], meta: str = "new"):
        self.notes = notes
        self.meta = meta


# ============================================================
# UTILS
# ============================================================
def is_strong_beat(beat_in_bar: float) -> bool:
    return abs(beat_in_bar - 0.0) < 1e-9 or abs(beat_in_bar - 2.0) < 1e-9


def wrap_degree_dist(a: int, b: int) -> int:
    d = (a - b) % 7
    return min(d, 7 - d)


def nearest_degree(target: int, candidates: List[int]) -> int:
    return min(candidates, key=lambda d: wrap_degree_dist(target, d))


def make_monophonic(notes: List[NoteEv], min_dur_beats: float = 0.10) -> List[NoteEv]:
    """
    Ensure no overlaps: truncate previous note to end at next note start.
    """
    notes = sorted(notes, key=lambda n: (n.start, n.dur))
    if not notes:
        return notes

    out = [notes[0]]
    for n in notes[1:]:
        prev = out[-1]
        prev_end = prev.start + prev.dur
        if n.start < prev_end:
            prev.dur = max(min_dur_beats, n.start - prev.start)
        out.append(n)

    cleaned = [n for n in out if n.dur >= min_dur_beats]
    return cleaned


def apply_harmonic_snapping(notes: List[NoteEv], chord_roots_by_bar: List[int], snap_edges: bool, snap_strong: bool) -> List[NoteEv]:
    """
    Snap lead degrees so they "sit" on chords:
    - first + last note in each bar -> chord tones
    - strong beats (1 & 3) -> chord tones
    chord_roots_by_bar length = PHRASE_BARS (2) for each phrase, degrees 0..6
    """
    notes = sorted(notes, key=lambda n: n.start)
    if not notes:
        return notes

    # group notes by bar
    bars = [[] for _ in range(PHRASE_BARS)]
    for n in notes:
        b = int(n.start // BEATS_PER_BAR)
        if 0 <= b < PHRASE_BARS:
            bars[b].append(n)

    for b in range(PHRASE_BARS):
        root = chord_roots_by_bar[b]
        chord_tones = [root, (root + 2) % 7, (root + 4) % 7]

        if bars[b]:
            if snap_edges:
                # first note in bar
                bars[b][0].deg = nearest_degree(bars[b][0].deg, chord_tones)
                # last note in bar
                bars[b][-1].deg = nearest_degree(bars[b][-1].deg, chord_tones)

            if snap_strong:
                for n in bars[b]:
                    beat_in_bar = n.start % BEATS_PER_BAR
                    if is_strong_beat(beat_in_bar):
                        n.deg = nearest_degree(n.deg, chord_tones)

    return notes


# ============================================================
# PROGRESSION ENGINE (4-chord loop forever)
# ============================================================
class ProgressionEngine:
    """
    Outputs chord roots as scale degrees (0..6) per bar.
    Fixed 4-chord loop, repeated forever.
    """
    def __init__(self, mode: str):
        self.mode = mode
        self.loop = self._select_loop(mode)

    def _select_loop(self, mode: str) -> List[int]:
        # degrees are scale degrees, not absolute semitones
        # House-friendly defaults:
        if mode == "major":
            return [0, 4, 5, 3]      # I - V - vi - IV
        if mode == "minor":
            return [0, 5, 2, 6]      # i - VI - III - VII
        if mode == "dorian":
            return [0, 6, 3, 0]      # i - VII - IV - i
        if mode == "mixolydian":
            return [0, 6, 3, 0]      # I - VII - IV - I-ish
        if mode == "harmonic_minor":
            return [0, 5, 2, 4]      # i - VI - III - V
        # fallback
        return [0, 5, 2, 6]

    def chord_root_for_bar(self, global_bar: int) -> int:
        return self.loop[global_bar % 4]


# ============================================================
# MOTIF GENERATOR + TRANSFORMS
# ============================================================
class MotifGenerator:
    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_new(self, style: StyleParams) -> Motif:
        notes: List[NoteEv] = []
        last_deg: Optional[int] = None

        for bar in range(PHRASE_BARS):
            bar_start = bar * BEATS_PER_BAR
            num = self.rng.randint(style.min_notes, style.max_notes)

            for _ in range(num):
                onset = bar_start + self.rng.choice([0, 0.5, 1, 1.5, 2, 2.5, 3])
                dur = self.rng.choice([0.5, 1])

                if last_deg is not None and self.rng.random() < style.step_bias:
                    deg = (last_deg + self.rng.choice([-1, 1])) % 7
                else:
                    deg = self.rng.randint(0, 6)

                vel = self.rng.randint(80, 110)
                notes.append(NoteEv(onset, dur, deg, vel))
                last_deg = deg

        notes = make_monophonic(notes, min_dur_beats=0.10)
        return Motif(notes, meta="new")

    def transform(self, motif: Motif, style: StyleParams) -> Motif:
        # choose one transformation
        choices = ["transpose", "rhythm_nudge", "ornament"]
        weights = [style.w_transpose, style.w_rhythm_nudge, style.w_ornament]
        t = self.rng.choices(choices, weights=weights, k=1)[0]

        notes = [NoteEv(n.start, n.dur, n.deg, n.vel) for n in motif.notes]
        meta = f"reuse_{t}"

        if t == "transpose":
            shift = self.rng.choice([-2, -1, 1, 2])
            for n in notes:
                n.deg = (n.deg + shift) % 7

        elif t == "rhythm_nudge":
            k = min(2, len(notes))
            idxs = self.rng.sample(range(len(notes)), k=k) if k > 0 else []
            for i in idxs:
                delta = self.rng.choice([-0.5, 0.5, -0.25, 0.25])
                s = notes[i].start + delta
                # clamp to phrase bounds (keep onsets inside [0, 8))
                s = max(0.0, min(PHRASE_BEATS - 0.5, s))
                notes[i].start = s
            notes.sort(key=lambda n: n.start)

        elif t == "ornament":
            # add a quick approach note before a strong-beat note (if space)
            strong = [n for n in notes if is_strong_beat(n.start % BEATS_PER_BAR)]
            if strong:
                target = self.rng.choice(strong)
                ornament_start = target.start - 0.5  # an 8th before
                if ornament_start >= 0.0:
                    approach_deg = (target.deg + self.rng.choice([-1, 1])) % 7
                    notes.append(NoteEv(ornament_start, 0.5, approach_deg, max(50, target.vel - 25)))
                    notes.sort(key=lambda n: n.start)

        notes = make_monophonic(notes, min_dur_beats=0.10)
        return Motif(notes, meta=meta)


# ============================================================
# MOTIF MEMORY
# ============================================================
@dataclass
class MemoryItem:
    motif: Motif
    times_used: int = 0
    last_used_phrase: int = -999


class MotifMemory:
    def __init__(self):
        self.items: List[MemoryItem] = []

    def add(self, motif: Motif, phrase_idx: int):
        self.items.append(MemoryItem(motif=motif, times_used=0, last_used_phrase=phrase_idx))

    def pick(self, phrase_idx: int, rng: random.Random, recent_block: int) -> Optional[MemoryItem]:
        candidates = [it for it in self.items if (phrase_idx - it.last_used_phrase) >= recent_block]
        if not candidates:
            return None
        weights = [1.0 + 0.35 * it.times_used for it in candidates]
        return rng.choices(candidates, weights=weights, k=1)[0]


# ============================================================
# ENGINE
# ============================================================
class Engine:
    def __init__(self):
        outs = mido.get_output_names()
        if MIDI_OUT_NAME not in outs:
            raise RuntimeError(f"MIDI port not found.\nWanted: {MIDI_OUT_NAME}\nAvailable: {outs}")

        self.out = mido.open_output(MIDI_OUT_NAME)
        self.active_notes = set()

        self.rng = random.Random()
        self.gen = MotifGenerator(self.rng)
        self.mem = MotifMemory()

        self.phrase_idx = 0
        self.global_bar = 0  # increments by 2 each phrase

    def send_on(self, pitch: int, vel: int, ch: int):
        self.out.send(mido.Message('note_on', note=int(pitch), velocity=int(vel), channel=int(ch)))
        self.active_notes.add((int(pitch), int(ch)))

    def send_off(self, pitch: int, ch: int):
        self.out.send(mido.Message('note_off', note=int(pitch), velocity=0, channel=int(ch)))
        self.active_notes.discard((int(pitch), int(ch)))

    def panic(self):
        for pitch, ch in list(self.active_notes):
            self.send_off(pitch, ch)

    def apply_swing(self, onset_beats: float, style: StyleParams) -> float:
        # Swing only offbeats at +1/2 beat positions (8th-note swing feel)
        if style.swing > 0 and abs((onset_beats % 1) - 0.5) < 1e-9:
            return onset_beats + style.swing
        return onset_beats

    def choose_motif(self, style: StyleParams, chord_roots_phrase: List[int]) -> Motif:
        """
        Memory logic:
        - with prob reuse_prob, pick motif from memory (not too recent) and transform
        - else generate new
        Then apply harmonic snapping (bar edges + strong beats) so motif fits chords.
        """
        reuse = (len(self.mem.items) > 0 and self.rng.random() < style.reuse_prob)

        if reuse:
            item = self.mem.pick(self.phrase_idx, self.rng, style.recent_block_phrases)
            if item is not None:
                m = self.gen.transform(item.motif, style)
                item.times_used += 1
                item.last_used_phrase = self.phrase_idx
                # apply chord-fit snapping AFTER transform
                m.notes = apply_harmonic_snapping(
                    m.notes,
                    chord_roots_by_bar=chord_roots_phrase,
                    snap_edges=style.snap_bar_edges,
                    snap_strong=style.snap_strong_beats
                )
                m.notes = make_monophonic(m.notes, min_dur_beats=0.10)
                self.mem.add(m, self.phrase_idx)
                return m

        m = self.gen.generate_new(style)
        # apply chord-fit snapping for new motifs too
        m.notes = apply_harmonic_snapping(
            m.notes,
            chord_roots_by_bar=chord_roots_phrase,
            snap_edges=style.snap_bar_edges,
            snap_strong=style.snap_strong_beats
        )
        m.notes = make_monophonic(m.notes, min_dur_beats=0.10)
        self.mem.add(m, self.phrase_idx)
        return m

    def run(self, style: StyleParams, bars: Optional[int] = None, with_chords: bool = False):
        bpm = style.bpm
        spb = 60.0 / bpm
        scale = ScaleEngine(style.tonic_midi, style.scale_mode)
        prog = ProgressionEngine(style.scale_mode)

        print(f"\nPre-roll: {PREROLL_SECONDS} seconds. Arm tracks + press Record.")
        for i in range(PREROLL_SECONDS, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
        print("GO!\n")

        total_phrases = float('inf') if bars is None else max(1, bars // PHRASE_BARS)
        start_phrase = self.phrase_idx

        try:
            while (self.phrase_idx - start_phrase) < total_phrases:
                # chord roots for the 2 bars of this phrase
                chord_roots_phrase = [
                    prog.chord_root_for_bar(self.global_bar + 0),
                    prog.chord_root_for_bar(self.global_bar + 1),
                ]

                motif = self.choose_motif(style, chord_roots_phrase)
                events = []

                # -------------------------
                # LEAD (channel 0) - MONO
                # -------------------------
                for n in motif.notes:
                    onset = self.apply_swing(n.start, style)
                    pitch = scale.degree_to_midi(n.deg, octave=0)
                    events.append((onset, True, pitch, n.vel, CH_LEAD))
                    events.append((onset + n.dur, False, pitch, 0, CH_LEAD))

                if with_chords:
                    # -------------------------
                    # CHORDS (channel 1) - POLY (1 chord per bar from progression)
                    # BASS  (channel 2) - MONO, follows chord root
                    # -------------------------
                    for bar in range(PHRASE_BARS):
                        bar_start = bar * BEATS_PER_BAR
                        bar_end = bar_start + BEATS_PER_BAR

                        root = chord_roots_phrase[bar]
                        triad = [root, (root + 2) % 7, (root + 4) % 7]

                        # chords
                        for deg in triad:
                            p = scale.degree_to_midi(deg, octave=0)
                            events.append((bar_start, True, p, 70, CH_CHORDS))
                            events.append((bar_end, False, p, 0, CH_CHORDS))

                        # bass (root, one octave down)
                        bass_pitch = scale.degree_to_midi(root, octave=-1)
                        events.append((bar_start, True, bass_pitch, 95, CH_BASS))
                        events.append((bar_end, False, bass_pitch, 0, CH_BASS))

                # schedule for this phrase
                events.sort(key=lambda e: e[0])
                phrase_start_time = time.time()

                for offset, is_on, pitch, vel, ch in events:
                    target = phrase_start_time + (offset * spb)
                    while True:
                        dt = target - time.time()
                        if dt <= 0:
                            break
                        time.sleep(min(0.001, dt))

                    if is_on:
                        self.send_on(pitch, vel, ch)
                    else:
                        self.send_off(pitch, ch)

                # advance
                self.phrase_idx += 1
                self.global_bar += PHRASE_BARS

        except KeyboardInterrupt:
            print("\nStopped by user.")
        finally:
            self.panic()


# ============================================================
# MAIN
# ============================================================
def main():
    eng = Engine()

    presets = list(STYLE_PRESETS.keys())
    print("Choose Preset:")
    for i, p in enumerate(presets, 1):
        print(f"{i}. {p}")
    p_idx = int(input("Preset number: ").strip()) - 1
    p_idx = max(0, min(p_idx, len(presets) - 1))
    style = STYLE_PRESETS[presets[p_idx]]

    print("\n1. Motif only")
    print("2. Motif + Chords + Bass")
    with_chords = int(input("Choice: ").strip()) == 2

    modes = list(SCALES.keys())
    print("\nChoose Scale:")
    for i, m in enumerate(modes, 1):
        print(f"{i}. {m}")
    s_idx = int(input("Scale number: ").strip()) - 1
    s_idx = max(0, min(s_idx, len(modes) - 1))
    style.scale_mode = modes[s_idx]

    bars_in = input("\nBars (8/16/32 or blank infinite): ").strip()
    bars = None if bars_in == "" else int(bars_in)

    print(f"\nPreset: {style.name} | BPM: {style.bpm} | Mode: {style.scale_mode}")

    eng.run(style, bars=bars, with_chords=with_chords)


if __name__ == "__main__":
    main()
