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
        """Verify all six phases are defined."""
        assert Phase.INTRO.value == "intro"
        assert Phase.BUILD.value == "build"
        assert Phase.PEAK.value == "peak"
        assert Phase.SUSTAIN.value == "sustain"
        assert Phase.RELEASE.value == "release"
        assert Phase.OUTRO.value == "outro"

    def test_phase_members(self):
        """Each phase has expected name."""
        assert Phase.INTRO.name == "INTRO"
        assert Phase.BUILD.name == "BUILD"
        assert Phase.PEAK.name == "PEAK"
        assert Phase.SUSTAIN.name == "SUSTAIN"
        assert Phase.RELEASE.name == "RELEASE"
        assert Phase.OUTRO.name == "OUTRO"


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_constructor(self):
        """Default constructor creates matrix with default transitions."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None

    def test_default_all_phases_in_matrix(self):
        """Default matrix includes all six phases."""
        matrix = PhaseTransitionMatrix()
        m = matrix.matrix
        for phase in Phase:
            assert phase in m

    def test_rows_contain_only_valid_phases(self):
        """Each transition entry references valid Phase values."""
        matrix = PhaseTransitionMatrix()
        m = matrix.matrix
        for from_phase, transitions in m.items():
            for to_phase, prob in transitions:
                assert isinstance(to_phase, Phase)
                assert 0.0 <= prob <= 1.0

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.dub_techno()
        assert matrix is not None

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.ambient()
        assert matrix is not None

    def test_style_factory_dub_techno(self):
        """StyleFactory creates dub_techno matrix."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None

    def test_style_factory_ambient(self):
        """StyleFactory creates ambient matrix."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None

    def test_style_factory_club(self):
        """StyleFactory creates club matrix."""
        matrix = StyleFactory.create("club")
        assert matrix is not None

    def test_style_factory_all_night(self):
        """StyleFactory creates all_night matrix."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None

    def test_invalid_style_raises(self):
        """Invalid style should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("invalid_style")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_generate_sequence_returns_all_phases_eventually(self):
        """Generate enough sequences to see all phases."""
        matrix = PhaseTransitionMatrix()
        seen = set()
        for _ in range(200):
            seq = matrix.generate_sequence(10)
            seen.update(seq)
        assert len(seen) >= 4  # should see most phases

    def test_generate_sequence_length(self):
        """Generate sequence of specified length."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10)
        assert len(seq) == 10

    def test_generate_sequence_starts_with_intro(self):
        """Generated sequence starts with intro by default."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5)
        assert seq[0] == Phase.INTRO

    def test_generate_sequence_custom_start(self):
        """Generated sequence can start with a custom phase."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5, start=Phase.PEAK)
        assert seq[0] == Phase.PEAK

    def test_sequence_all_valid_phases(self):
        """All elements in generated sequence are valid Phase values."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(100)
        for phase in seq:
            assert isinstance(phase, Phase)

    def test_matrix_property_returns_copy(self):
        """Matrix property returns a copy, not the internal reference."""
        matrix = PhaseTransitionMatrix()
        m1 = matrix.matrix
        m2 = matrix.matrix
        assert m1 is not m2


class TestPhaseStyleBehavior:
    """Tests for differences in transition behavior across styles."""

    def test_dub_techno_has_longer_sections(self):
        """Dub techno has higher sustain self-transition than club."""
        dub_matrix = PhaseTransitionMatrix.dub_techno()
        club_matrix = StyleFactory.create("club")

        # Dub techno should have higher sustain self-transition probability
        dub_sustain_self = 0.0
        club_sustain_self = 0.0
        for to_phase, prob in dub_matrix.matrix[Phase.SUSTAIN]:
            if to_phase == Phase.SUSTAIN:
                dub_sustain_self = prob
        for to_phase, prob in club_matrix.matrix[Phase.SUSTAIN]:
            if to_phase == Phase.SUSTAIN:
                club_sustain_self = prob

        assert dub_sustain_self > club_sustain_self

    def test_ambient_has_longer_intros(self):
        """Ambient style has higher intro self-transition than dub techno."""
        ambient_matrix = PhaseTransitionMatrix.ambient()
        dub_matrix = PhaseTransitionMatrix.dub_techno()

        ambient_intro_self = 0.0
        dub_intro_self = 0.0
        for to_phase, prob in ambient_matrix.matrix[Phase.INTRO]:
            if to_phase == Phase.INTRO:
                ambient_intro_self = prob
        for to_phase, prob in dub_matrix.matrix[Phase.INTRO]:
            if to_phase == Phase.INTRO:
                dub_intro_self = prob

        assert ambient_intro_self > dub_intro_self

    def test_outro_does_not_transition(self):
        """Once in outro, the sequence should loop or stay."""
        matrix = PhaseTransitionMatrix()
        matrix_impl = matrix.matrix[Phase.OUTRO]
        phases = [p for p, _ in matrix_impl]
        # OUTRO should exist in its own transitions
        assert Phase.OUTRO in phases
        assert Phase.INTRO in phases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
