"""Tests for Markov phase transition matrix generation."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
)


class TestPhaseEnum:
    """Tests for the Phase enum representing musical sections."""

    def test_phase_enums(self):
        """Verify all six phases are defined."""
        assert Phase.INTRO == 1
        assert Phase.BUILD == 2
        assert Phase.CASCADE == 3
        assert Phase.SUSTAIN == 4
        assert Phase.ROLLBACK == 5
        assert Phase.OUTRO == 6

    def test_phase_names(self):
        """Each phase has a readable name attribute."""
        assert "intro" in Phase.INTRO.name.lower()
        assert "build" in Phase.BUILD.name.lower()
        assert "cascade" in Phase.CASCADE.name.lower()
        assert "sustain" in Phase.SUSTAIN.name.lower()
        assert "rollback" in Phase.ROLLBACK.name.lower()
        assert "outro" in Phase.OUTRO.name.lower()


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_factory(self):
        """Factory method creates default matrix."""
        matrix = PhaseTransitionMatrix.create_default()
        assert matrix is not None
        assert matrix.transition_matrix.shape == (6, 6)

    def test_default_all_phases_defined(self):
        """Default factory includes all six phases."""
        matrix = PhaseTransitionMatrix.create_default()
        for from_phase in Phase:
            for to_phase in Phase:
                assert matrix.get_transition_probability(from_phase, to_phase) >= 0.0
                assert matrix.get_transition_probability(from_phase, to_phase) <= 1.0

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to 1.0."""
        matrix = PhaseTransitionMatrix.create_default()
        for from_phase in Phase:
            row_sum = 0.0
            for to_phase in Phase:
                row_sum += matrix.get_transition_probability(from_phase, to_phase)
            assert abs(row_sum - 1.0) < 1e-10  # Allow for floating point error

    def test_dub_techno_factory(self):
        """Factory for dubtechno style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.create_style(PhaseStyle.DUB_TECHNO)
        assert matrix is not None

        # Dub techno should have longer sections (sustains after builds)
        build_to_sustain = matrix.get_transition_probability(Phase.BUILD, Phase.SUSTAIN)
        assert build_to_sustain > 0.0

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.create_style(PhaseStyle.AMBIENT)
        assert matrix is not None

        # Ambient should have longer intros and cascades
        intro_to_cascade = matrix.get_transition_probability(Phase.INTRO, Phase.CASCADE)
        assert intro_to_cascade > 0.0

    def test_club_factory(self):
        """Factory for club style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.create_style(PhaseStyle.CLUB)
        assert matrix is not None

        # Club style should have more rapid transitions and energy
        sustain_to_cascade = matrix.get_transition_probability(Phase.SUSTAIN, Phase.CASCADE)
        assert sustain_to_cascade > 0.0

    def test_all_night_factory(self):
        """Factory for allnight style uses appropriate transitions."""
        matrix = PhaseTransitionMatrix.create_style(PhaseStyle.ALL_NIGHT)
        assert matrix is not None

        # All night style should avoid outro
        outro_from_any = sum(
            matrix.get_transition_probability(p, Phase.OUTRO) for p in Phase
        )
        assert outro_from_any < 0.1

    def test_invalid_style_raises(self):
        """Invalid phase style should raise ValueError."""
        with pytest.raises(ValueError):
            PhaseTransitionMatrix.create_style(PhaseStyle.INVALID)


class TestPhaseTransitionMatrixBehavior:
    """Tests for Markov chain behavior with transition matrix."""

    def test_get_next_phase(self):
        """Get next phase in the sequence."""
        matrix = PhaseTransitionMatrix.create_default()
        next_phase = matrix.get_next_phase(Phase.INTRO)
        assert isinstance(next_phase, Phase)

    def test_all_phases_can_be_next(self):
        """Every phase can potentially follow any other phase."""
        matrix = PhaseTransitionMatrix.create_default()
        seen_transitions = {}

        for _ in range(1000):
            current = Phase.INTRO
            for i in range(10):
                next_phase = matrix.get_next_phase(current)
                pair = (current, next_phase)
                seen_transitions[pair] = seen_transitions.get(pair, 0) + 1
                current = next_phase

        # We should see some transitions between various phases
        assert len(seen_transitions) > 1

    def test_outro_does_not_transition(self):
        """Once in outro, the sequence stays in outro."""
        matrix = PhaseTransitionMatrix.create_default()
        next_phase = matrix.get_next_phase(Phase.OUTRO)
        assert next_phase == Phase.OUTRO


class TestPhaseStyleBehavior:
    """Tests for differences in transition behavior across styles."""

    def test_dub_techno_has_longer_sections(self):
        """Dub techno has longer sections compared to club."""
        dub_matrix = PhaseTransitionMatrix.create_style(PhaseStyle.DUB_TECHNO)
        club_matrix = PhaseTransitionMatrix.create_style(PhaseStyle.CLUB)

        # Compare self-transition probabilities (probability to stay in same phase)
        dub_self = dub_matrix.get_transition_probability(Phase.SUSTAIN, Phase.SUSTAIN)
        club_self = club_matrix.get_transition_probability(Phase.SUSTAIN, Phase.SUSTAIN)

        # Dub techno should have higher self-transition (longer sustains)
        assert dub_self > club_self

    def test_ambient_has_longer_intros(self):
        """Ambient style has longer intros compared to dub techno."""
        ambient_matrix = PhaseTransitionMatrix.create_style(PhaseStyle.AMBIENT)
        dub_matrix = PhaseTransitionMatrix.create_style(PhaseStyle.DUB_TECHNO)

        # Compare intro self-transition
        ambient_intro = ambient_matrix.get_transition_probability(Phase.INTRO, Phase.INTRO)
        dub_intro = dub_matrix.get_transition_probability(Phase.INTRO, Phase.INTRO)

        assert ambient_intro > dub_intro

    def test_all_night_avoids_outro(self):
        """All night style has very low probability of reaching outro."""
        all_night_matrix = PhaseTransitionMatrix.create_style(PhaseStyle.ALL_NIGHT)
        dub_matrix = PhaseTransitionMatrix.create_default()

        # Sum all probabilities of transitioning to outro
        all_night_outro = sum(
            all_night_matrix.get_transition_probability(p, Phase.OUTRO) for p in Phase
        )
        dub_outro = sum(dub_matrix.get_transition_probability(p, Phase.OUTRO) for p in Phase)

        assert all_night_outro < dub_outro


class TestTransitionStyleIntegration:
    """Tests for integration with TransitionStyle enum."""

    def test_transition_style_maps_to_phase_style(self):
        """TransitionStyle aligns with PhaseStyle options."""
        # This ensures consistency between styling enums
        assert TransitionStyle.DEFAULT.value == "default"
        assert TransitionStyle.DUB_TECHNO.value == "dub_techno"
        assert TransitionStyle.AMBIENT.value == "ambient"
        assert TransitionStyle.CLUB.value == "club"
        assert TransitionStyle.ALL_NIGHT.value == "all_night"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
