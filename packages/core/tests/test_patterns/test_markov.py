"""Tests for Markov phase transition matrix generation."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


class TestPhaseEnum:
    """Tests for the Phase enum representing musical sections."""

    def test_phase_enums(self):
        """Verify all six phases are defined as string values."""
        assert Phase.INTRO == "intro"
        assert Phase.BUILD == "build"
        assert Phase.PEAK == "peak"
        assert Phase.SUSTAIN == "sustain"
        assert Phase.RELEASE == "release"
        assert Phase.OUTRO == "outro"

    def test_phase_names(self):
        """Each phase has a readable name attribute."""
        assert "intro" in Phase.INTRO.name.lower()
        assert "build" in Phase.BUILD.name.lower()
        assert "peak" in Phase.PEAK.name.lower()
        assert "sustain" in Phase.SUSTAIN.name.lower()
        assert "release" in Phase.RELEASE.name.lower()
        assert "outro" in Phase.OUTRO.name.lower()


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_construction(self):
        """Default constructor creates matrix with all six phases."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None
        assert len(matrix.matrix) == 6

    def test_default_all_phases_defined(self):
        """Default matrix includes all six phases with valid probabilities."""
        matrix = PhaseTransitionMatrix()
        all_phases = list(Phase)
        for from_phase in all_phases:
            transitions = matrix.matrix.get(from_phase, [])
            for to_phase, prob in transitions:
                assert 0.0 <= prob <= 1.0

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to 1.0."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            transitions = matrix.matrix.get(from_phase, [])
            row_sum = sum(prob for _, prob in transitions)
            assert abs(row_sum - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None

        # Dub techno should have sustain after builds
        transitions = matrix.matrix.get(Phase.BUILD, [])
        sustain_prob = sum(prob for p, prob in transitions if p == Phase.SUSTAIN)
        assert sustain_prob > 0.0

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None

        # Ambient should have longer intros (high self-transition)
        transitions = matrix.matrix.get(Phase.INTRO, [])
        intro_self = sum(prob for p, prob in transitions if p == Phase.INTRO)
        assert intro_self > 0.3

    def test_club_factory(self):
        """Factory for club style uses appropriate transitions."""
        matrix = StyleFactory.create("club")
        assert matrix is not None

        # Club style should have transitions
        transitions = matrix.matrix.get(Phase.SUSTAIN, [])
        assert len(transitions) > 0

    def test_all_night_factory(self):
        """Factory for allnight style uses appropriate transitions."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None

        # All night style should have transitions defined
        transitions = matrix.matrix.get(Phase.INTRO, [])
        assert len(transitions) > 0

    def test_invalid_style_raises(self):
        """Invalid phase style should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("non_existent_style")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_get_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_sequence_generation(self):
        """Generate a sequence of phases."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10)
        assert len(seq) == 10
        assert isinstance(seq[0], Phase)

    def test_sequence_starts_at_intro(self):
        """Default sequence starts at INTRO."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5)
        assert seq[0] == Phase.INTRO

    def test_outro_can_transition(self):
        """Outro can transition to other phases (INTRO, BUILD)."""
        matrix = PhaseTransitionMatrix()
        transitions = matrix.matrix.get(Phase.OUTRO, [])
        # OUTRO has transitions to INTRO, BUILD, (and optionally itself)
        has_non_outro = any(p != Phase.OUTRO for p, _ in transitions)
        assert has_non_outro


class TestStyleFactory:
    """Tests for StyleFactory convenience methods."""

    def test_all_styles_available(self):
        """All predefined styles are accessible."""
        for style in ["dub_techno", "ambient", "club", "all_night"]:
            matrix = StyleFactory.create(style)
            assert isinstance(matrix, PhaseTransitionMatrix)
            assert len(matrix.matrix) == 6

    def test_style_matrices_differ(self):
        """Different styles produce different transition matrices."""
        dub = StyleFactory.create("dub_techno")
        ambient = StyleFactory.create("ambient")

        # Compare a specific transition
        dub_intro = dub.matrix.get(Phase.INTRO, [])
        ambient_intro = ambient.matrix.get(Phase.INTRO, [])
        assert dub_intro != ambient_intro
