"""Claude API client wrapper: prompt building and README drafting."""

from __future__ import annotations

import anthropic

from readme_forge.summary import RepoSummary

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096

PROMPT_TEMPLATE = """You are drafting a README.md for a code repository based on the \
structured summary below. Write clear, accurate Markdown using only the information \
given; do not invent facts not supported by the summary.

Include exactly these sections, in this order, using Markdown headings: {sections}

Repository summary (JSON):
{summary_json}

Return only the Markdown document, with no commentary before or after it.
"""


def build_prompt(summary: RepoSummary, sections: list[str]) -> str:
    """Build the drafting prompt from a bounded RepoSummary and requested sections."""
    return PROMPT_TEMPLATE.format(sections=", ".join(sections), summary_json=summary.to_json())


def draft_readme(
    summary: RepoSummary,
    sections: list[str],
    model: str,
    api_key: str,
) -> str:
    """Call the Claude API and return the drafted README as Markdown.

    Raises anthropic SDK exceptions on failure; callers map them to friendly
    errors via errors.py.
    """
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(summary, sections)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))
