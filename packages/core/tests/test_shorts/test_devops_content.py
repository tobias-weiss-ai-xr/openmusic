"""Tests for devops_content module."""
import pytest

from openmusic.shorts.devops_content import (
    TIPS,
    get_random_tip,
    get_tips_by_category,
    get_tips_by_language,
    get_tips_by_keyword,
    search_tips,
    get_categories,
    get_languages,
    DevOpsTip,
)


def test_tips_is_list_of_devops_tips():
    assert len(TIPS) > 0
    for t in TIPS:
        assert isinstance(t, DevOpsTip)


def test_tip_has_required_fields():
    for t in TIPS:
        assert isinstance(t.title, str) and len(t.title) > 0
        assert isinstance(t.code, str) and len(t.code) > 0
        assert isinstance(t.language, str) and len(t.language) > 0
        assert isinstance(t.description, str) and len(t.description) > 0
        assert isinstance(t.category, str) and len(t.category) > 0
        assert isinstance(t.source, str) and len(t.source) > 0


def test_get_random_tip():
    tip = get_random_tip()
    assert tip in TIPS


def test_get_random_tip_with_seed():
    t1 = get_random_tip(seed=42)
    t2 = get_random_tip(seed=42)
    assert t1 == t2
    assert t1.title == t2.title
    assert t1.code == t2.code


def test_get_tips_by_category():
    docker_tips = get_tips_by_category("docker")
    assert len(docker_tips) > 0
    assert all(t.category.lower() == "docker" for t in docker_tips)


def test_get_tips_by_language():
    python_tips = get_tips_by_language("python")
    assert len(python_tips) > 0
    assert all(t.language.lower() == "python" for t in python_tips)


def test_get_categories():
    categories = get_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert len(set(categories)) == len(categories)


def test_get_languages():
    languages = get_languages()
    assert isinstance(languages, list)
    assert len(languages) > 0
    assert len(set(languages)) == len(languages)