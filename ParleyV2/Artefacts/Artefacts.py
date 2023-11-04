from dataclasses import dataclass


@dataclass
class Timing:
    start64th: int = None
    duration64ths: int = None
    tuplet_duration64ths: int = None
    tuplet_length: int = None
    tuplet_note_type: str = None
    tuplet_note_duration64ths: int = None


@dataclass
class MidiTiming:
    on_tick: int = None
    duration_ticks: int = None
    off_tick: int = None


@dataclass
class Scale:
    pitch_classes: [] = None
    tonic_letter: str = None
    scale_type: str = None


@dataclass
class Composition:
    title: str = None
    subtitle: str = None
    random_seed: int = None
    num_episodes: int = None
    num_bars: int = None
    beats_per_bar: int = None
    bars: [] = None
    episodes_hash: {} = None
    bars_hash: {} = None
    note_sequences_hash: {} = None
    chords_hash: {} = None
    track_notes_hash: {} = None
    episode_track_notes_hash: {} = None


@dataclass
class Episode:
    episode_num: int = None
    form_id: str = None
    num_bars: int = None


@dataclass
class Bar:
    bar_num: int = None
    episode_bar_num: int = None
    start64th: int = None
    start_tick: int = None
    end_tick: int = None
    duration_ticks: int = None
    num_beats: int = None
    tick_timings: [] = None
    directions: str = None
    chord_nums: [] = None
    note_sequences: [] = None
    episode_num: int = None
    margin_comments: [] = None
    directions: [] = None
    mtg_vectors: [] = None
    mtg_activation_tags: [] = None


@dataclass
class Chord:
    pitches: [] = None
    scale_name: str = None
    chord_name: str = None
    timing: Timing = None
    cnro_used: [] = None
    chord_num: int = None
    bar_num: int = None


@dataclass
class NoteSequence:
    next_note_sequence_num = 0 # This is a global variable
    note_sequence_num: int = None
    instrument_num: int = None
    voice_id: str = None
    track_num: int = None
    channel_num: int = None
    notes: [] = None
    bar_num: int = None


@dataclass
class Note:
    pitch: int = None
    volume: int = None
    timing: Timing = None
    midi_timing: Timing = None
    cutoff_prop: int = None
    note_type: str = None
    tie_type: str = None
    beam_type: str = None
    score_colour: str = None
    sorted_pitch_classes: [] = None
    chord_num: int = None
    note_sequence_num: int = None
    bar_num: int = None
    track_note_num: int = None
    episode_track_note_num: int = None
    pause_64ths: int = None


@dataclass
class MarginComment:
    comment_text: str = None
    comment_colour: str = None
