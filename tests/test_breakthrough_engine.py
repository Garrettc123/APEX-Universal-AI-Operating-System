"""Tests for the BreakthroughEngine."""

import pytest

from src.breakthrough_engine import DOMAINS, WEIGHTS, Breakthrough, BreakthroughEngine


def test_weights_sum_to_one():
    assert pytest.approx(sum(WEIGHTS.values())) == 1.0


def test_engine_initialization():
    engine = BreakthroughEngine(seed=1)
    assert engine.breakthroughs == []


async def test_generate_returns_scored_breakthrough():
    engine = BreakthroughEngine(seed=42)
    bt = await engine.generate()
    assert isinstance(bt, Breakthrough)
    assert bt.domain in DOMAINS
    assert 0.0 <= bt.novelty <= 1.0
    assert 0.0 <= bt.impact <= 1.0
    assert 0.0 <= bt.feasibility <= 1.0
    assert 0.0 <= bt.score <= 1.0
    assert engine.breakthroughs == [bt]


async def test_generate_with_specific_domain():
    engine = BreakthroughEngine(seed=7)
    bt = await engine.generate(domain="fintech")
    assert bt.domain == "fintech"


async def test_generate_unknown_domain_raises():
    engine = BreakthroughEngine(seed=7)
    with pytest.raises(ValueError):
        await engine.generate(domain="time_travel")


async def test_seed_makes_output_reproducible():
    a = await BreakthroughEngine(seed=99).generate()
    b = await BreakthroughEngine(seed=99).generate()
    assert a.title == b.title
    assert a.score == pytest.approx(b.score)


async def test_portfolio_is_ranked_desc():
    engine = BreakthroughEngine(seed=3)
    portfolio = await engine.generate_portfolio(count=8)
    assert len(portfolio) == 8
    scores = [b.score for b in portfolio]
    assert scores == sorted(scores, reverse=True)


async def test_get_top_limits_results():
    engine = BreakthroughEngine(seed=3)
    await engine.generate_portfolio(count=10)
    assert len(engine.get_top(3)) == 3


def test_to_dict_is_serializable():
    bt = Breakthrough(
        id="bt-0",
        title="t",
        domain="robotics",
        method="m",
        novelty=0.5,
        impact=0.6,
        feasibility=0.7,
        score=0.58,
    )
    d = bt.to_dict()
    assert d["domain"] == "robotics"
    assert d["score"] == 0.58
