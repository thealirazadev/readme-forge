"""Tests for prompt building and README drafting, with the anthropic client mocked."""

from __future__ import annotations

from unittest import mock

import pytest

from readme_forge.api import DEFAULT_MODEL, build_prompt, draft_readme
from readme_forge.summary import RepoSummary


@pytest.fixture
def summary() -> RepoSummary:
    return RepoSummary(root_name="sample", file_count=3)


def test_build_prompt_includes_sections_and_summary_json(summary: RepoSummary) -> None:
    prompt = build_prompt(summary, ["overview", "usage"])
    assert "overview, usage" in prompt
    assert '"root_name": "sample"' in prompt


def _fake_response(text: str):
    block = mock.Mock()
    block.text = text
    response = mock.Mock()
    response.content = [block]
    return response


def test_draft_readme_returns_text_from_response(summary: RepoSummary) -> None:
    with mock.patch("readme_forge.api.anthropic.Anthropic") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.messages.create.return_value = _fake_response("# Sample\n")

        result = draft_readme(summary, ["overview"], DEFAULT_MODEL, "sk-ant-test")

    assert result == "# Sample\n"
    mock_client_cls.assert_called_once_with(api_key="sk-ant-test")
    mock_client.messages.create.assert_called_once()
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["model"] == DEFAULT_MODEL


def test_draft_readme_ignores_non_text_blocks(summary: RepoSummary) -> None:
    non_text_block = mock.Mock(spec=[])
    text_block = mock.Mock()
    text_block.text = "body"
    response = mock.Mock()
    response.content = [non_text_block, text_block]

    with mock.patch("readme_forge.api.anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = response
        result = draft_readme(summary, ["overview"], DEFAULT_MODEL, "sk-ant-test")

    assert result == "body"
