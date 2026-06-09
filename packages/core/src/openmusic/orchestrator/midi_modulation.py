from dataclasses import dataclass, field


@dataclass
class ModulationPattern:
    velocities: list[int] = field(default_factory=list)
    timings: list[float] = field(default_factory=list)


def generate_modulation_pattern(
    bpm: int = 125,
    steps: int = 16,
) -> ModulationPattern:
    import random

    hits = max(4, steps // 3)
    step_indices = sorted(random.sample(range(steps), hits))

    velocities: list[int] = []
    timings: list[float] = []

    beat_duration = 60.0 / bpm

    for step_idx in step_indices:
        velocity = random.randint(40, 100)
        velocities.append(velocity)
        timings.append(step_idx * beat_duration)

    return ModulationPattern(velocities=velocities, timings=timings)


def midi_to_modulation_values(
    pattern: ModulationPattern,
    target_range: tuple[float, float] = (0.0, 1.0),
) -> list[float]:
    if not pattern.velocities:
        return []

    lo, hi = target_range
    return [
        lo + (v / 127.0) * (hi - lo)
        for v in pattern.velocities
    ]


def get_modulation_for_segment(
    index: int,
    total: int,
    bpm: int = 125,
) -> dict[str, float]:
    import random

    rng = random.Random(index * 137 + bpm)

    num_hits = rng.randint(2, 5)
    velocities = [rng.randint(40, 100) for _ in range(num_hits)]

    avg_vel = sum(velocities) / len(velocities) if velocities else 64

    return {
        "delay_feedback_mod": 0.2 + (avg_vel / 127.0) * 0.6,
        "reverb_mix_mod": 0.3 + (avg_vel / 127.0) * 0.5,
        "filter_cutoff_mod": 200 + (avg_vel / 127.0) * 1800,
    }
