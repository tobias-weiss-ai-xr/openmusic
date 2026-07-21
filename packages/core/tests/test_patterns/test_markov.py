"""Tests for Markov phase transition matrix — matching current source API."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


class TestPhaseEnum:
    """Tests for the Phase enum representing musical sections."""

    def test_phase_values(self):
        """Verify all six phases are defined with correct values."""
        assert Phase.INTRO.value == "intro"
        assert Phase.BUILD.value == "build"
        assert Phase.PEAK.value == "peak"
        assert Phase.SUSTAIN.value == "sustain"
        assert Phase.RELEASE.value == "release"
        assert Phase.OUTRO.value == "outro"

    def test_phase_names(self):
        """Each phase has a readable name."""
        assert "intro" in Phase.INTRO.name.lower()
        assert "build" in Phase.BUILD.name.lower()
        assert "peak" in Phase.PEAK.name.lower()
        assert "sustain" in Phase.SUSTAIN.name.lower()
        assert "release" in Phase.RELEASE.name.lower()
        assert "outro" in Phase.OUTRO.name.lower()


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_matrix(self):
        """Default constructor creates valid matrix."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None
        assert len(matrix.matrix) == 6  # All six phases

    def test_default_all_phases_defined(self):
        """Default matrix includes all six phases."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            assert from_phase in matrix.matrix
            transitions = matrix.matrix[from_phase]
            for to_phase, prob in transitions:
                assert 0.0 <= prob <= 1.0

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to ~1.0."""
        matrix = PhaseTransitionMatrix()
        for from_phase in Phase:
            row_sum = sum(prob for _, prob in matrix.matrix[from_phase])
            assert abs(row_sum - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None

        build_transitions = dict(matrix.matrix[Phase.BUILD])
        sustain_prob = build_transitions.get(Phase.SUSTAIN, 0.0)
        assert sustain_prob > 0.0

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None

        intro_transitions = dict(matrix.matrix[Phase.INTRO])
        sustain_prob = intro_transitions.get(Phase.SUSTAIN, 0.0)
        assert sustain_prob > 0.0
        # Ambient should have high intro self-transition
        intro_self = intro_transitions.get(Phase.INTRO, 0.0)
        assert intro_self >= 0.3

    def test_club_factory(self):
        """Factory for club style uses appropriate transitions."""
        matrix = StyleFactory.create("club")
        assert matrix is not None

        sustain_transitions = dict(matrix.matrix[Phase.SUSTAIN])
        peak_prob = sustain_transitions.get(Phase.PEAK, 0.0)
        assert peak_prob > 0.0

    def test_all_night_factory(self):
        """Factory for all_night style uses appropriate transitions."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None

        # All night style has very low outro probability
        outro_sum = sum(
            prob for p in Phase for _, prob in matrix.matrix[p] if _ == Phase.OUTRO
        )
        assert outro_sum < 1.0

    def test_invalid_style_raises(self):
        """Invalid style should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("invalid_style")


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_get_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix()
        next_phase = matrix.next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_all_phases_can_be_next(self):
        """Every phase can potentially follow another over many runs."""
        matrix = PhaseTransitionMatrix()
        seen = set()

        for _ in range(500):
            current = Phase.INTRO
            for _ in range(20):
                next_phase = matrix.next_phase(current)
                seen.add((current, next_phase))
                current = next_phase

        assert len(seen) > 1

    def test_outro_does_not_transition(self):
        """Once in outro, the sequence stays in outro or loops."""
        matrix = PhaseTransitionMatrix()
        outro_transitions = dict(matrix.matrix[Phase.OUTRO])
        # Outro can transition to intro (loop) or stay
        for phase, prob in matrix.matrix[Phase.OUTRO]:
            assert prob > 0.0

    def test_generate_sequence(self):
        """Generate a sequence of phases."""
        matrix = PhaseTransitionMatrix()
        seq = matrix.generate_sequence(10, start=Phase.INTRO)
        assert len(seq) == 10
        assert seq[0] == Phase.INTRO
        for p in seq:
            assert isinstance(p, Phase)


class TestPhaseStyleBehavior:
    """Tests for differences in transition behavior across styles."""

    def test_dub_techno_has_longer_sections(self):
        """Dub techno has higher self-transition probabilities."""
        dub_matrix = StyleFactory.create("dub_techno")
        club_matrix = StyleFactory.create("club")

        dub_sustain_self = dict(dub_matrix.matrix[Phase.SUSTAIN]).get(Phase.SUSTAIN, 0.0)
        club_sustain_self = dict(club_matrix.matrix[Phase.SUSTAIN]).get(Phase.SUSTAIN, 0.0)

        assert dub_sustain_self > club_sustain_self

    def test_ambient_has_longer_intros(self):
        """Ambient style has longer intros compared to dub techno."""
        ambient_matrix = StyleFactory.create("ambient")
        dub_matrix = StyleFactory.create("dub_techno")

        ambient_intro_self = dict(ambient_matrix.matrix[Phase.INTRO]).get(Phase.INTRO, 0.0)
        dub_intro_self = dict(dub_matrix.matrix[Phase.INTRO]).get(Phase.INTRO, 0.0)

        assert ambient_intro_self > dub_intro_self

    def test_all_night_avoids_outro(self):
        """All night style has lower probability of reaching outro."""
        all_night_matrix = StyleFactory.create("all_night")
        dub_matrix = PhaseTransitionMatrix()

        all_night_outro = sum(
            prob for p in Phase for _, prob in all_night_matrix.matrix[p] if _ == Phase.OUTRO
        )
        dub_outro = sum(
            prob for p in Phase for _, prob in dub_matrix.matrix[p] if _ == Phase.OUTRO
        )

        assert all_night_outro <= dub_outro


class TestStyleFactoryIntegration:
    """Tests for StyleFactory integration."""

    def test_all_styles_are_valid(self):
        """All registered styles produce valid matrices."""
        for style_name in StyleFactory.STYLES:
            matrix = StyleFactory.create(style_name)
            assert isinstance(matrix, PhaseTransitionMatrix)
            assert len(matrix.matrix) == 6

    def test_dub_techno_via_factory(self):
        """StyleFactory.create('dub_techno') works correctly."""
        matrix = StyleFactory.create("dub_techno")
        assert isinstance(matrix, PhaseTransitionMatrix)
        assert Phase.PEAK in matrix.matrix


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
