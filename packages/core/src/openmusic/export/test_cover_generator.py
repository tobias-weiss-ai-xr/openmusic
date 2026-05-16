# packages/core/src/openmusic/export/test_cover_generator.py
import pytest
import re
from openmusic.export.cover_generator import CoverGenerator, MixCoverConfig


def test_same_seed_produces_same_svg():
    """Identical seed always produces byte-identical SVG."""
    config = MixCoverConfig(key="Am", bpm=125, length=3600.0, title="Test Mix")
    gen1 = CoverGenerator(config)
    gen2 = CoverGenerator(config)
    svg1 = gen1.generate_svg()
    svg2 = gen2.generate_svg()
    assert svg1 == svg2


def test_different_keys_produce_different_svg():
    """Different keys (different hue) produce visually different SVG."""
    config_am = MixCoverConfig(key="Am", bpm=125, length=3600.0, title="Test")
    config_dm = MixCoverConfig(key="Dm", bpm=125, length=3600.0, title="Test")
    svg_am = CoverGenerator(config_am).generate_svg()
    svg_dm = CoverGenerator(config_dm).generate_svg()
    assert svg_am != svg_dm


def test_beam_count_scales_with_bpm():
    """Higher BPM = more beams."""
    config_low = MixCoverConfig(key="Am", bpm=120, length=3600.0, title="Test")
    config_high = MixCoverConfig(key="Am", bpm=140, length=3600.0, title="Test")
    svg_low = CoverGenerator(config_low).generate_svg()
    svg_high = CoverGenerator(config_high).generate_svg()
    # Count <line elements inside beam groups
    beams_low = len(re.findall(r'<line[^>]*stroke="#1a', svg_low))
    beams_high = len(re.findall(r'<line[^>]*stroke="#1a', svg_high))
    assert beams_high > beams_low


def test_minor_key_lower_saturation():
    """Minor keys have lower saturation than major keys."""
    config_minor = MixCoverConfig(key="Am", bpm=125, length=3600.0, title="Test")
    config_major = MixCoverConfig(key="A", bpm=125, length=3600.0, title="Test")
    gen_minor = CoverGenerator(config_minor)
    gen_major = CoverGenerator(config_major)
    assert gen_minor.saturation < gen_major.saturation