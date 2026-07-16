"""Tests for Markov phase transition matrix generation."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


def _get_prob(matrix, from_phase, to_phase):
    """Look up transition probability between two phases."""
    transitions = matrix.matrix.get(from_phase, [])
    for phase, prob in transitions:
        if phase == to_phase:
            return prob
    return 0.0


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

    def test_default_factory(self):
        """Default constructor creates matrix."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None

    def test_default_all_phases_defined(self):
        """Default matrix includes all six phases."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            assert from_phase in matrix.matrix

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to 1.0."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            transitions = matrix.matrix.get(from_phase, [])
            row_sum = sum(weight for _, weight in transitions)
            assert abs(row_sum - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.dub_techno()
        assert matrix is not None

        build_to_sustain = _get_prob(matrix, Phase.BUILD, Phase.SUSTAIN)
        assert build_to_sustain > 0.0

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.ambient()
        assert matrix is not None

        intro_to_sustain = _get_prob(matrix, Phase.INTRO, Phase.SUSTAIN)
        assert intro_to_sustain > 0.0

    def test_club_factory(self):
        """Factory for club style uses appropriate transitions."""
        matrix = StyleFactory.create("club")
        assert matrix is not None

        sustain_to_peak = _get_prob(matrix, Phase.SUSTAIN, Phase.PEAK)
        assert sustain_to_peak > 0.0

    def test_all_night_factory(self):
        """Factory for allnight style uses appropriate transitions."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None

        outro_from_any = sum(
            _get_prob(matrix, p, Phase.OUTRO) for p in Phase
        )
        assert outro_from_any < 0.75

    def test_invalid_style_raises(self):
        """Invalid phase style should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("nonexistent")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_get_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_all_phases_can_be_next(self):
        """Every phase can potentially follow any other phase."""
        matrix = PhaseTransitionMatrix()
        seen_transitions = {}

        for _ in range(1000):
            current = Phase.INTRO
            for _ in range(10):
                next_phase = matrix.next_phase(current)
                pair = (current, next_phase)
                seen_transitions[pair] = seen_transitions.get(pair, 0) + 1
                current = next_phase

        assert len(seen_transitions) > 1

    def test_outro_does_not_loop(self):
        """Outro has defined transitions (not an absorbing state)."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.OUTRO)
        assert isinstance(next_phase, Phase)


class TestPhaseStyleBehavior:
    """Tests for differences in transition behavior across styles."""

    def test_dub_techno_has_longer_sections(self):
        """Dub techno has longer sections compared to club."""
        dub_matrix = PhaseTransitionMatrix.dub_techno()
        club_matrix = StyleFactory.create("club")

        dub_self = _get_prob(dub_matrix, Phase.SUSTAIN, Phase.SUSTAIN)
        club_self = _get_prob(club_matrix, Phase.SUSTAIN, Phase.SUSTAIN)

        assert dub_self > club_self

    def test_ambient_has_longer_intros(self):
        """Ambient style has longer intros compared to dub techno."""
        ambient_matrix = PhaseTransitionMatrix.ambient()
        dub_matrix = PhaseTransitionMatrix.dub_techno()

        ambient_intro = _get_prob(ambient_matrix, Phase.INTRO, Phase.INTRO)
        dub_intro = _get_prob(dub_matrix, Phase.INTRO, Phase.INTRO)

        assert ambient_intro > dub_intro

    def test_all_night_avoids_outro(self):
        """All night style has very low probability of reaching outro."""
        all_night_matrix = StyleFactory.create("all_night")
        dub_matrix = PhaseTransitionMatrix()

        all_night_outro = sum(
            _get_prob(all_night_matrix, p, Phase.OUTRO) for p in Phase
        )
        dub_outro = sum(
            _get_prob(dub_matrix, p, Phase.OUTRO) for p in Phase
        )

        assert all_night_outro < dub_outro


class TestStyleFactoryIntegration:
    """Tests for StyleFactory with predefined style names."""

    def test_style_factory_creates_dub_techno(self):
        """StyleFactory.create('dub_techno') produces a valid matrix."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_creates_ambient(self):
        """StyleFactory.create('ambient') produces a valid matrix."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_creates_club(self):
        """StyleFactory.create('club') produces a valid matrix."""
        matrix = StyleFactory.create("club")
        assert matrix is not None
        assert isinstance(matrix, PhaseTransitionMatrix)

    def test_style_factory_creates_all_night(self):
        """StyleFactory.create('all_night') produces a valid matrix."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None
        assert isinstance(matrix, PhaseTransitionMatrix)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
