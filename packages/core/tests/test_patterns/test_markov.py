"""Tests for Markov phase transition matrix — matching current API."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


class TestPhaseEnum:
    """Tests for the Phase enum."""

    def test_phase_values(self):
        """Verify all six phases are defined as string values."""
        assert Phase.INTRO == "intro"
        assert Phase.BUILD == "build"
        assert Phase.PEAK == "peak"
        assert Phase.SUSTAIN == "sustain"
        assert Phase.RELEASE == "release"
        assert Phase.OUTRO == "outro"

    def test_phase_members(self):
        """All six phase members exist."""
        assert len(list(Phase)) == 6


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_constructor(self):
        """Default constructor creates matrix with default transitions."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None

    def test_matrix_has_all_phases(self):
        """matrix property contains all six phases as keys."""
        matrix = PhaseTransitionMatrix()
        assert len(matrix.matrix) == 6
        for phase in Phase:
            assert phase in matrix.matrix

    def test_row_sums_to_one(self):
        """Each row in transition matrix sums to 1.0."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            transitions = matrix.matrix[from_phase]
            row_sum = sum(prob for _, prob in transitions)
            assert abs(row_sum - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """dub_techno classmethod creates a valid matrix."""
        matrix = PhaseTransitionMatrix.dub_techno()
        assert matrix is not None
        assert len(matrix.matrix) == 6

    def test_ambient_factory(self):
        """ambient classmethod creates a valid matrix."""
        matrix = PhaseTransitionMatrix.ambient()
        assert matrix is not None
        assert len(matrix.matrix) == 6


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior."""

    def test_next_phase_returns_phase(self):
        """next_phase returns a valid Phase for any input."""
        matrix = PhaseTransitionMatrix()
        for current in Phase:
            next_p = matrix.next_phase(current)
            assert isinstance(next_p, Phase)
            assert next_p in Phase

    def test_generate_sequence_length(self):
        """generate_sequence returns correct number of phases."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10)
        assert len(seq) == 10
        assert all(isinstance(p, Phase) for p in seq)

    def test_generate_sequence_starts_correctly(self):
        """generate_sequence starts with the given start phase."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(5, start=Phase.BUILD)
        assert seq[0] == Phase.BUILD

    def test_outro_can_transition_to_intro(self):
        """Outro has a non-zero transition probability to intro."""
        matrix = PhaseTransitionMatrix()
        transitions = matrix.matrix[Phase.OUTRO]
        has_intro = any(t[0] == Phase.INTRO for t in transitions)
        assert has_intro

    def test_outro_is_reachable(self):
        """Outro appears in at least one from-phase transition list."""
        matrix = PhaseTransitionMatrix()
        all_to_phases = set()
        for transitions in matrix.matrix.values():
            for to_phase, _ in transitions:
                all_to_phases.add(to_phase)
        assert Phase.OUTRO in all_to_phases


class TestStyleFactory:
    """Tests for StyleFactory."""

    def test_create_dub_techno(self):
        """StyleFactory.create('dub_techno') returns a PhaseTransitionMatrix."""
        matrix = StyleFactory.create("dub_techno")
        assert isinstance(matrix, PhaseTransitionMatrix)
        assert len(matrix.matrix) == 6

    def test_create_ambient(self):
        """StyleFactory.create('ambient') returns a PhaseTransitionMatrix."""
        matrix = StyleFactory.create("ambient")
        assert isinstance(matrix, PhaseTransitionMatrix)
        assert len(matrix.matrix) == 6

    def test_create_club(self):
        """StyleFactory.create('club') returns a PhaseTransitionMatrix."""
        matrix = StyleFactory.create("club")
        assert isinstance(matrix, PhaseTransitionMatrix)
        assert len(matrix.matrix) == 6

    def test_create_all_night(self):
        """StyleFactory.create('all_night') returns a PhaseTransitionMatrix."""
        matrix = StyleFactory.create("all_night")
        assert isinstance(matrix, PhaseTransitionMatrix)
        assert len(matrix.matrix) == 6

    def test_invalid_style_raises(self):
        """Invalid style name raises ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("invalid_style")


class TestTransitionMatrixIntegration:
    """Tests that matrices work together with generate_sequence."""

    def test_dub_techno_generates_sequence(self):
        """dub_techno matrix generates a valid sequence."""
        matrix = PhaseTransitionMatrix.dub_techno()
        seq = matrix.generate_sequence(20)
        assert len(seq) == 20
        assert all(p in Phase for p in seq)

    def test_style_factory_generates_valid_sequence(self):
        """Each StyleFactory style generates valid sequences."""
        for style in ("dub_techno", "ambient", "club", "all_night"):
            matrix = StyleFactory.create(style)
            seq = matrix.generate_sequence(10)
            assert len(seq) == 10
            assert all(p in Phase for p in seq)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
