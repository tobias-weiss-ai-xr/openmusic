"""Tests for Markov phase transition matrix generation."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


class TestPhaseEnum:
    """Tests for the Phase enum representing musical sections."""

    def test_phase_values(self):
        """Verify all six phases have correct string values."""
        assert Phase.INTRO.value == "intro"
        assert Phase.BUILD.value == "build"
        assert Phase.PEAK.value == "peak"
        assert Phase.SUSTAIN.value == "sustain"
        assert Phase.RELEASE.value == "release"
        assert Phase.OUTRO.value == "outro"

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

    def test_default_constructor(self):
        """Default constructor creates a matrix with all six phases."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None
        assert set(matrix.matrix.keys()) == {
            Phase.INTRO, Phase.BUILD, Phase.PEAK,
            Phase.SUSTAIN, Phase.RELEASE, Phase.OUTRO,
        }

    def test_dub_techno_factory(self):
        """Factory for dub techno style creates a valid matrix."""
        matrix = PhaseTransitionMatrix.dub_techno()
        assert matrix is not None

    def test_ambient_factory(self):
        """Factory for ambient style creates a valid matrix."""
        matrix = PhaseTransitionMatrix.ambient()
        assert matrix is not None

    def test_style_factory_dub_techno(self):
        """StyleFactory creates dub_techno style matrix."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_ambient(self):
        """StyleFactory creates ambient style matrix."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None

    def test_style_factory_club(self):
        """StyleFactory creates club style matrix."""
        matrix = StyleFactory.create("club")
        assert matrix is not None

    def test_style_factory_all_night(self):
        """StyleFactory creates all_night style matrix."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None

    def test_style_factory_invalid_raises(self):
        """Invalid style name should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("nonexistent_style")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_generate_sequence(self):
        """Generate a sequence of phases."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10)
        assert len(seq) == 10
        assert seq[0] == Phase.INTRO

    def test_next_phase_outro_returns_valid(self):
        """Get next phase from outro."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.OUTRO)
        assert isinstance(next_phase, Phase)

    def test_matrix_property_returns_dict(self):
        """The matrix property returns a dict keyed by Phase."""
        matrix = PhaseTransitionMatrix()
        assert isinstance(matrix.matrix, dict)
        assert Phase.INTRO in matrix.matrix

    def test_all_phases_have_transitions(self):
        """Every phase has at least one possible transition."""
        matrix = PhaseTransitionMatrix()
        for phase in Phase:
            transitions = matrix.matrix.get(phase, [])
            assert len(transitions) > 0


class TestPhaseTransitionSequence:
    """Tests for sequence generation properties."""

    def test_sequence_starts_at_intro_by_default(self):
        """Default start phase is INTRO."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5)
        assert seq[0] == Phase.INTRO

    def test_sequence_custom_start(self):
        """Sequence can start at a custom phase."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5, start=Phase.SUSTAIN)
        assert seq[0] == Phase.SUSTAIN


class TestStyleFactoryMatrix:
    """Tests for style-specific matrix properties."""

    def test_matrix_contents_vary_by_style(self):
        """Different styles produce different transition matrices."""
        dub = StyleFactory.create("dub_techno")
        club = StyleFactory.create("club")
        assert dub.matrix != club.matrix


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
