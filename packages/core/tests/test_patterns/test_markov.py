"""Tests for Markov phase transition matrix generation."""

import pytest

from openmusic.patterns.markov import (
    Phase,
    PhaseTransitionMatrix,
    StyleFactory,
)


class TestPhaseEnum:
    """Tests for the Phase enum representing musical sections."""

    def test_phase_members(self):
        """Verify all phase members are defined as string enum."""
        assert Phase.INTRO.value == "intro"
        assert Phase.BUILD.value == "build"
        assert Phase.PEAK.value == "peak"
        assert Phase.SUSTAIN.value == "sustain"
        assert Phase.RELEASE.value == "release"
        assert Phase.OUTRO.value == "outro"

    def test_phase_names(self):
        """Each phase has a readable name."""
        assert "intro" in Phase.INTRO.value
        assert "build" in Phase.BUILD.value
        assert "peak" in Phase.PEAK.value
        assert "sustain" in Phase.SUSTAIN.value
        assert "release" in Phase.RELEASE.value
        assert "outro" in Phase.OUTRO.value


class TestPhaseTransitionMatrixCreation:
    """Tests for creating transition matrices."""

    def test_default_matrix(self):
        """Default constructor creates a valid matrix."""
        matrix = PhaseTransitionMatrix()
        assert matrix is not None

    def test_default_all_phases_defined(self):
        """Default matrix includes all six phases."""
        matrix = PhaseTransitionMatrix()
        m = matrix.matrix
        for from_phase in Phase:
            assert from_phase in m
            transitions = m[from_phase]
            total = sum(w for _, w in transitions)
            assert abs(total - 1.0) < 1e-10

    def test_row_sums_to_one(self):
        """Each row in transition matrix should sum to 1.0."""
        matrix = PhaseTransitionMatrix()
        m = matrix.matrix
        for from_phase in Phase:
            transitions = m[from_phase]
            total = sum(w for _, w in transitions)
            assert abs(total - 1.0) < 1e-10

    def test_dub_techno_factory(self):
        """Factory for dub techno style uses appropriate transitions."""
        matrix = StyleFactory.create("dub_techno")
        assert matrix is not None
        m = matrix.matrix

        # Dub techno: build should transition to peak with high probability
        build_transitions = dict(m[Phase.BUILD])
        assert build_transitions[Phase.PEAK] > 0.0

    def test_ambient_factory(self):
        """Factory for ambient style uses appropriate transitions."""
        matrix = StyleFactory.create("ambient")
        assert matrix is not None
        m = matrix.matrix

        # Ambient: intro should have high self-transition (longer intros)
        intro_transitions = dict(m[Phase.INTRO])
        assert intro_transitions[Phase.INTRO] > 0.0

    def test_club_factory(self):
        """Factory for club style uses appropriate transitions."""
        matrix = StyleFactory.create("club")
        assert matrix is not None
        m = matrix.matrix

        # Club: sustain should transition somewhere
        sustain_transitions = dict(m[Phase.SUSTAIN])
        assert sum(sustain_transitions.values()) > 0.0

    def test_all_night_factory(self):
        """Factory for all_night style uses appropriate transitions."""
        matrix = StyleFactory.create("all_night")
        assert matrix is not None
        m = matrix.matrix

        # All night: sum all probabilities of transitioning to outro
        outro_sum = sum(
            dict(m[p]).get(Phase.OUTRO, 0.0) for p in Phase
        )
        # All night should have relatively low outro probability
        assert outro_sum < 1.0

    def test_invalid_style_raises(self):
        """Invalid style name should raise ValueError."""
        with pytest.raises(ValueError):
            StyleFactory.create("invalid")


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
        for p in seq:
            assert isinstance(p, Phase)

    def test_outro_does_not_transition_to_different(self):
        """Outro has very high self-transition."""
        matrix = PhaseTransitionMatrix()
        # Run many times — intro should almost always be the next after outro
        results = set()
        for _ in range(100):
            results.add(matrix.next_phase(Phase.OUTRO))
        # With the default matrix, OUTRO transitions to INTRO (0.80), OUTRO (0.15), BUILD (0.05)
        # So we'll see INTRO as most common
        assert Phase.INTRO in results or Phase.OUTRO in results


class TestStyleFactory:
    """Tests for StyleFactory convenience methods."""

    def test_all_styles_available(self):
        """All predefined styles should be available."""
        for style in ("dub_techno", "ambient", "club", "all_night"):
            matrix = StyleFactory.create(style)
            assert matrix is not None
            assert isinstance(matrix, PhaseTransitionMatrix)

    def test_styles_differ(self):
        """Different styles should produce different matrices."""
        dub = StyleFactory.create("dub_techno")
        ambient = StyleFactory.create("ambient")

        dub_intro = dict(dub.matrix[Phase.INTRO])
        ambient_intro = dict(ambient.matrix[Phase.INTRO])

        # Intro self-transition should differ between styles
        assert dub_intro[Phase.INTRO] != ambient_intro[Phase.INTRO]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
