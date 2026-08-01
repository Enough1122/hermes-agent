"""Tests: streaming token accounting fallback when the provider returns no
usage data (#12023).

Providers whose streaming backend ignores ``stream_options.include_usage``
(MiniMax via OpenRouter, and other aggregators whose upstream doesn't support
usage reporting in streaming mode) deliver a normal completion with no usage
chunk. Without a fallback the assembled response carries ``usage=None`` and the
downstream accounting block (gated on ``if response.usage:``) is skipped
entirely — the session silently records 0/0 tokens despite running normally.

The fix synthesizes an estimated usage object in the streaming finalizer so
the existing accounting path executes unchanged.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.chat_completion_helpers import _estimate_missing_stream_usage
from agent.usage_pricing import normalize_usage


def _make_stream_chunk(content=None, finish_reason=None, model=None, usage=None):
    delta = SimpleNamespace(
        content=content, tool_calls=None, reasoning_content=None, reasoning=None
    )
    choice = SimpleNamespace(index=0, delta=delta, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], model=model, usage=usage)


def _make_empty_chunk(model=None, usage=None):
    """Build a chunk with no choices (usage-only final chunk)."""
    return SimpleNamespace(choices=[], model=model, usage=usage)


# ---------------------------------------------------------------------------
# Unit tests for the synthesis helper
# ---------------------------------------------------------------------------


def test_helper_synthesizes_nonzero_usage_from_messages_and_content():
    """A real request + response yields a non-zero estimated usage object."""
    agent = SimpleNamespace(model="minimax/minimax-m2.7", provider="openrouter")
    api_kwargs = {
        "messages": [
            {"role": "user", "content": "Please explain quantum tunneling in detail."},
        ]
    }
    usage = _estimate_missing_stream_usage(agent, api_kwargs, "Quantum tunneling is...", None)

    assert usage is not None
    assert usage.prompt_tokens > 0
    assert usage.completion_tokens > 0


def test_helper_returns_none_for_fully_empty_estimate():
    """No messages and no content → None (preserve prior behavior)."""
    agent = SimpleNamespace(model="m", provider="p")
    usage = _estimate_missing_stream_usage(agent, {"messages": []}, "", None)
    assert usage is None


def test_helper_estimate_flows_through_normalize_usage_nonzero():
    """The synthesized object is shaped so normalize_usage produces non-zero
    canonical buckets — proving the downstream accounting block (which gates on
    `response.usage` being truthy, then normalizes) would actually run and
    record tokens instead of skipping silently."""
    agent = SimpleNamespace(model="minimax/minimax-m2.7", provider="openrouter")
    api_kwargs = {"messages": [{"role": "user", "content": "a" * 400}]}
    usage = _estimate_missing_stream_usage(agent, api_kwargs, "b" * 200, None)

    assert usage is not None
    canonical = normalize_usage(usage, provider="openrouter", api_mode="chat_completions")
    assert canonical.input_tokens > 0
    assert canonical.output_tokens > 0
    assert canonical.total_tokens == canonical.input_tokens + canonical.output_tokens


def test_helper_includes_reasoning_in_output_estimate():
    """Reasoning text is counted toward the output estimate (major cost center
    for reasoning models)."""
    agent = SimpleNamespace(model="m", provider="p")
    api_kwargs = {"messages": [{"role": "user", "content": "hi"}]}
    without_reasoning = _estimate_missing_stream_usage(agent, api_kwargs, "x", None)
    with_reasoning = _estimate_missing_stream_usage(agent, api_kwargs, "x", "y" * 1000)
    assert with_reasoning.completion_tokens > without_reasoning.completion_tokens


# ---------------------------------------------------------------------------
# Integration: the streaming finalizer attaches synthesized usage when the
# provider's stream carries no usage chunk (the MiniMax scenario).
# ---------------------------------------------------------------------------


@patch("run_agent.AIAgent._create_request_openai_client")
@patch("run_agent.AIAgent._close_request_openai_client")
def test_streaming_synthesizes_usage_when_provider_returns_none(mock_close, mock_create):
    """A stream with no usage chunk still yields a non-None, non-zero usage."""
    from run_agent import AIAgent

    # MiniMax-via-OpenRouter scenario: content + finish_reason delivered, but
    # NO usage-only final chunk (the provider ignored include_usage).
    chunks = [
        _make_stream_chunk(content="Hello"),
        _make_stream_chunk(content=" world", finish_reason="stop", model="minimax/minimax-m2.7"),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter(chunks)
    mock_create.return_value = mock_client

    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="minimax/minimax-m2.7",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    agent.api_mode = "chat_completions"
    agent._interrupt_requested = False

    api_kwargs = {
        "messages": [
            {"role": "user", "content": "Say hello to the world loudly and clearly."}
        ]
    }
    response = agent._interruptible_streaming_api_call(api_kwargs)

    assert response.choices[0].message.content == "Hello world"
    # The fix: usage is synthesized instead of None.
    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0


@patch("run_agent.AIAgent._create_request_openai_client")
@patch("run_agent.AIAgent._close_request_openai_client")
def test_streaming_preserves_real_usage_when_provider_returns_it(mock_close, mock_create):
    """When the provider DOES return usage, the synthesized fallback is not taken."""
    from run_agent import AIAgent

    chunks = [
        _make_stream_chunk(content="Hello", finish_reason="stop", model="test-model"),
        _make_empty_chunk(usage=SimpleNamespace(prompt_tokens=42, completion_tokens=7)),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter(chunks)
    mock_create.return_value = mock_client

    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="test/model",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    agent.api_mode = "chat_completions"
    agent._interrupt_requested = False

    response = agent._interruptible_streaming_api_call(
        {"messages": [{"role": "user", "content": "hi"}]}
    )

    # Real provider usage is preserved verbatim, not overwritten by an estimate.
    assert response.usage is not None
    assert response.usage.prompt_tokens == 42
    assert response.usage.completion_tokens == 7
