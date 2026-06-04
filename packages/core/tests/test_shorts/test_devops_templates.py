"""Tests for devops_templates module."""
from pathlib import Path

from openmusic.shorts.devops_content import DevOpsTip
from openmusic.shorts.devops_templates import (
    render_devops_html,
    render_tip_html,
    render_code_only_html,
)


def test_render_devops_html_returns_string():
    html = render_devops_html(DevOpsTip(
        title="Test",
        code="echo 'hello'",
        language="bash",
        description="Test description",
        category="test",
        source="test",
    ))
    assert isinstance(html, str)
    assert len(html) > 500
    assert "<!DOCTYPE html>" in html
    assert "Test" in html
    assert "echo 'hello'" in html


def test_render_devops_html_contains_prism():
    html = render_devops_html(DevOpsTip(
        title="Test",
        code="print('hello')",
        language="python",
        description="Test",
        category="test",
        source="test",
    ))
    assert "prism.min.js" in html
    assert "class=\"language-python\"" in html


def test_render_tip_html():
    html = render_tip_html(DevOpsTip(
        title="Docker Run",
        code="docker run nginx",
        language="docker",
        description="Run nginx container",
        category="docker",
        source="test",
    ))
    assert "Docker Run" in html
    assert "docker run nginx" in html
    assert "Run nginx container" in html


def test_render_code_only_html():
    html = render_code_only_html(
        code="kubectl get pods",
        language="bash",
        title="List Pods",
    )
    assert "List Pods" in html
    assert "kubectl get pods" in html
    assert "class=\"language-bash\"" in html


def test_html_escaping():
    html = render_devops_html(DevOpsTip(
        title="Test <script>",
        code='echo "<script>"',
        language="bash",
        description="Test > &",
        category="test",
        source="test",
    ))
    assert "<script>" not in html or "&lt;script&gt;" in html
    assert "&lt;" in html
    assert "&gt;" in html