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
        """Verify all phases are defined."""
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

    def test_default_constructor(self):
        """Default constructor creates matrix with standard transitions."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None

    def test_default_all_phases_defined(self):
        """Default matrix includes all phases."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            transitions = matrix.matrix.get(from_phase)
            assert transitions is not None
            for to_phase, prob in transitions:
                assert 0.0 <= prob <= 1.0

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to 1.0."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            transitions = matrix.matrix.get(from_phase)
            if transitions:
                row_sum = sum(prob for _, prob in transitions)
                assert abs(row_sum - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.dub_techno()
        assert matrix is not None

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.ambient()
        assert matrix is not None

    def test_club_factory(self):
        """StyleFactory.create for club style."""
        matrix = StyleFactory.create("club")
        assert matrix is not None
        # Club should have shorter intro (lower self-transition)
        intro_transitions = dict(matrix.matrix[Phase.INTRO])
        assert intro_transitions[Phase.INTRO] < 0.30

    def test_all_night_factory(self):
        """StyleFactory.create for all_night style."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None
        # All night should transition away from OUTRO
        outro_transitions = dict(matrix.matrix[Phase.OUTRO])
        assert outro_transitions[Phase.INTRO] > 0.0

    def test_invalid_style_raises(self):
        """Invalid phase style should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("invalid")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_get_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_all_phases_can_be_next(self):
        """Every phase can potentially follow another."""
        matrix = PhaseTransitionMatrix()
        seen_transitions = set()

        for _ in range(1000):
            current = Phase.INTRO
            for _ in range(10):
                next_phase = matrix.next_phase(current)
                pair = (current.value, next_phase.value)
                seen_transitions.add(pair)
                current = next_phase

        assert len(seen_transitions) > 1

    def test_next_phase_is_valid(self):
        """next_phase always returns a valid Phase."""
        matrix = PhaseTransitionMatrix()
        for _ in range(100):
            result = matrix.next_phase(Phase.INTRO)
            assert isinstance(result, Phase)
            assert result in Phase

    def test_generate_sequence(self):
        """Generate a sequence of phases."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10)
        assert len(seq) == 10
        assert seq[0] == Phase.INTRO
        for p in seq:
            assert isinstance(p, Phase)
            assert p in Phase


class TestPhaseStyleBehavior:
    """Tests for differences in transition behavior across styles."""

    def test_dub_techno_has_longer_sections(self):
        """Dub techno has longer sections compared to club."""
        dub_matrix = PhaseTransitionMatrix.dub_techno()
        club_matrix = StyleFactory.create("club")

        dub_sustain_self = dict(dub_matrix.matrix[Phase.SUSTAIN])
        club_sustain_self = dict(club_matrix.matrix[Phase.SUSTAIN])

        dub_self = dub_sustain_self.get(Phase.SUSTAIN, 0)
        club_self = club_sustain_self.get(Phase.SUSTAIN, 0)

        # Dub techno should have higher self-transition (longer sustains)
        assert dub_self > club_self

    def test_ambient_has_longer_intros(self):
        """Ambient style has longer intros compared to dub techno."""
        ambient_matrix = PhaseTransitionMatrix.ambient()
        dub_matrix = PhaseTransitionMatrix.dub_techno()

        ambient_intro = dict(ambient_matrix.matrix[Phase.INTRO])
        dub_intro = dict(dub_matrix.matrix[Phase.INTRO])

        ambient_self = ambient_intro.get(Phase.INTRO, 0)
        dub_self = dub_intro.get(Phase.INTRO, 0)

        assert ambient_self > dub_self

    def test_all_night_avoids_outro(self):
        """All night style has lower probability of reaching outro."""
        all_night_matrix = StyleFactory.create("all_night")
        dub_matrix = PhaseTransitionMatrix.dub_techno()

        all_night_outro = sum(
            dict(all_night_matrix.matrix[p]).get(Phase.OUTRO, 0) for p in Phase
        )
        dub_outro = sum(
            dict(dub_matrix.matrix[p]).get(Phase.OUTRO, 0) for p in Phase
        )

        assert all_night_outro < dub_outro


class TestStyleFactory:
    """Tests for the StyleFactory class."""

    def test_style_factory_dub_techno(self):
        """StyleFactory.create returns dub_techno matrix."""
        matrix = StyleFactory.create("dub_techno")
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_ambient(self):
        """StyleFactory.create returns ambient matrix."""
        matrix = StyleFactory.create("ambient")
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_club(self):
        """StyleFactory.create returns club matrix."""
        matrix = StyleFactory.create("club")
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_all_night(self):
        """StyleFactory.create returns all_night matrix."""
        matrix = StyleFactory.create("all_night")
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_styles_are_different(self):
        """Different styles produce different matrixes."""
        dub = PhaseTransitionMatrix.dub_techno()
        ambient = PhaseTransitionMatrix.ambient()
        # Intro self-transition should differ
        dub_intro = dict(dub.matrix[Phase.INTRO])
        ambient_intro = dict(ambient.matrix[Phase.INTRO])
        assert dub_intro[Phase.INTRO] != ambient_intro[Phase.INTRO]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
