from ParleyV2.Artefacts.Artefacts import *
class Constants:

    chord_types_hash = {
        "maj": [4, 3],
        "min": [3, 4],
        "aug": [4, 4],
        "dim": [3, 3]
    }

    note_letters = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

    # From: https://en.wikipedia.org/wiki/List_of_musical_scales_and_modes
    scales_hash = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "double harmonic minor": [0, 2, 3, 6, 7, 8, 11],
        "lydian dominant": [0, 2, 4, 6, 7, 9, 10],
        "super lochrian": [0, 1, 3, 4, 6, 8, 10],
        "augmented": [0, 3, 4, 7, 8, 11],
        "bebop": [0, 2, 4, 5, 7, 9, 10, 11],
        "blues": [0, 3, 5, 6, 7, 10],
        "dorian mode": [0, 2, 3, 5, 7, 9, 10],
        "double harmonic": [0, 1, 4, 5, 7, 8, 11],
        "enigmatic": [0, 1, 4, 6, 8, 10, 11],
        "flamenco": [0, 1, 4, 5, 7, 8, 11],
        "gypsy": [0, 2, 3, 6, 7, 8, 10],
        "half diminished": [0, 2, 3, 5, 6, 8, 10],
        "harmonic major": [0, 2, 4, 5, 7, 8, 11],
        "harajoshi": [0, 4, 6, 7, 11],
        "hungarian minor": [0, 2, 3, 6, 7, 8, 11],
        "hungarian major": [0, 3, 4, 6, 7, 9, 10],
        "insen": [0, 1, 5, 7, 10],
        "istrian": [0, 1, 3, 4, 6, 7],
        "iwato": [0, 1, 5, 6, 10],
        "lochrian mode": [0, 1, 3, 5, 6, 8, 10],
        "lydian augmented": [0, 2, 4, 6, 8, 9, 11],
        "lydian diminished": [0, 2, 3, 6, 7, 9, 11],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "major lochrian": [0, 2, 4, 5, 6, 8, 10],
        "minor pentatonic": [0, 3, 5, 7, 10],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "neopolitan major": [0, 1, 3, 5, 7, 9, 11],
        "persian": [0, 1, 4, 5, 6, 8, 11],
        "phyrgian dominant": [0, 1, 4, 5, 7, 8, 10],
        "prometheus": [0, 2, 4, 6, 9, 10],
        "tritone": [0, 1, 4, 6, 7, 10],
        "two-semitone": [0, 1, 2, 6, 7, 8],
        "altered dorian": [0, 2, 3, 6, 7, 9, 10],
        "whole tone": [0, 2, 4, 6, 8, 10],
        "yo": [0, 3, 5, 7, 10]
    }
