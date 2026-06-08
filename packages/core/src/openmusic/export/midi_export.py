"""Export OpenMusic patterns to MIDI files."""

import random
from pathlib import Path
from typing import Optional

DEFAULT_MIDI_TEMPO = 120

NOTE_NAME_MAP = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def _midi_note_to_number(note: str | int) -> int:
    if isinstance(note, int):
        return note
    note = note.strip()
    if len(note) < 2:
        raise ValueError(f"Invalid note: {note}")
    name = note[:-1]
    octave = int(note[-1])
    semitone = NOTE_NAME_MAP.get(name)
    if semitone is None:
        raise ValueError(f"Unknown note name: {name}")
    return (octave + 1) * 12 + semitone


def _write_midi(
    notes: list[int],
    output_path: str | Path,
    bpm: int,
    durations: list[float],
    velocities: list[int],
) -> Path:
    from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

    mid = MidiFile(type=1)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm)))

    for n, d, v in zip(notes, durations, velocities):
        ticks = int(d * mid.ticks_per_beat)
        track.append(Message("note_on", note=n, velocity=v, time=0))
        track.append(Message("note_off", note=n, velocity=v, time=ticks))

    mid.save(str(output_path))
    return Path(output_path)


def pattern_to_isobar_sequence(
    note_values: list[int | str],
    durations: Optional[list[float]] = None,
    velocities: Optional[list[int]] = None,
):
    if not note_values:
        return None
    try:
        from isobar import Sequence
    except ImportError:
        return None

    notes = [_midi_note_to_number(n) if isinstance(n, str) else n for n in note_values]
    kwargs: dict = {}
    if durations is not None:
        kwargs["duration"] = durations
    if velocities is not None:
        kwargs["velocity"] = velocities
    return Sequence(notes, **kwargs)


def export_pattern_to_midi(
    note_values: list[int | str],
    output_path: str | Path,
    bpm: int = DEFAULT_MIDI_TEMPO,
    durations: Optional[list[float]] = None,
    velocities: Optional[list[int]] = None,
) -> Path:
    try:
        import isobar  # noqa: F401
    except ImportError:
        raise ImportError(
            "isobar is required for MIDI export. "
            "Install: pip install openmusic-core[midi]"
        )

    if not note_values:
        raise ValueError("note_values must not be empty")
    if velocities is not None and len(velocities) != len(note_values):
        raise ValueError(
            f"velocities length ({len(velocities)}) must be same length "
            f"as note_values ({len(note_values)})"
        )
    if durations is not None and len(durations) != len(note_values):
        raise ValueError(
            f"durations length ({len(durations)}) must be same length "
            f"as note_values ({len(note_values)})"
        )

    notes = [_midi_note_to_number(n) if isinstance(n, str) else n for n in note_values]

    if durations is None:
        durations_list = [1.0] * len(notes)
    else:
        durations_list = durations

    if velocities is None:
        velocities_list = [100] * len(notes)
    else:
        velocities_list = velocities

    return _write_midi(notes, output_path, bpm, durations_list, velocities_list)


def export_markov_chain_to_midi(
    transitions: dict[str | int, dict[str | int, float]],
    output_path: str | Path,
    steps: int = 32,
    start_state: Optional[str | int] = None,
    bpm: int = DEFAULT_MIDI_TEMPO,
) -> Path:
    if not transitions:
        raise ValueError("transitions dict must not be empty")

    states = list(transitions.keys())
    current = start_state if start_state is not None else random.choice(states)
    notes: list[str | int] = []

    for _ in range(steps):
        notes.append(current)
        next_options = transitions.get(current, {})
        if not next_options:
            current = random.choice(states)
        else:
            candidates = list(next_options.keys())
            weights = [next_options[c] for c in candidates]
            current = random.choices(candidates, weights=weights, k=1)[0]

    return export_pattern_to_midi(notes, output_path, bpm=bpm)
