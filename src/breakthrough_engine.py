"""APEX Breakthrough Engine

Generates, scores, and ranks candidate "breakthrough" ideas across domains.

HONESTY NOTE: this is a deterministic idea-generation and ranking *framework*,
not a system that produces real scientific or commercial breakthroughs. It
combines methods with domains and scores the combinations with explicit
heuristics (novelty, impact, feasibility). Use it to brainstorm and prioritize
R&D directions — then have humans validate them. Given a fixed ``seed`` the
output is fully reproducible, which is what makes it testable.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Scoring weights for the composite breakthrough score (must sum to 1.0).
WEIGHTS = {"novelty": 0.4, "impact": 0.4, "feasibility": 0.2}

# Per-domain base characteristics: (novelty_bias, impact_bias, feasibility_bias).
# Biases nudge the random draws so each domain has a distinct risk/reward shape.
DOMAINS: Dict[str, Dict[str, float]] = {
    "artificial_intelligence": {"novelty": 0.75, "impact": 0.85, "feasibility": 0.70},
    "biotechnology": {"novelty": 0.80, "impact": 0.90, "feasibility": 0.45},
    "clean_energy": {"novelty": 0.65, "impact": 0.88, "feasibility": 0.55},
    "advanced_materials": {"novelty": 0.70, "impact": 0.72, "feasibility": 0.50},
    "robotics": {"novelty": 0.60, "impact": 0.75, "feasibility": 0.65},
    "space_systems": {"novelty": 0.85, "impact": 0.70, "feasibility": 0.35},
    "fintech": {"novelty": 0.55, "impact": 0.68, "feasibility": 0.80},
    "climate_tech": {"novelty": 0.68, "impact": 0.92, "feasibility": 0.48},
}

# Reusable "method" primitives combined with a domain to form an idea.
METHODS: List[str] = [
    "self-supervised foundation models",
    "closed-loop autonomous experimentation",
    "differentiable simulation",
    "generative design search",
    "federated edge inference",
    "programmable biology",
    "high-throughput screening",
    "reinforcement-learned control",
]


@dataclass
class Breakthrough:
    """A scored candidate breakthrough idea."""

    id: str
    title: str
    domain: str
    method: str
    novelty: float
    impact: float
    feasibility: float
    score: float = 0.0
    rationale: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "method": self.method,
            "novelty": round(self.novelty, 4),
            "impact": round(self.impact, 4),
            "feasibility": round(self.feasibility, 4),
            "score": round(self.score, 4),
            "rationale": self.rationale,
        }


def _score(novelty: float, impact: float, feasibility: float) -> float:
    """Weighted composite score in [0, 1]."""
    return WEIGHTS["novelty"] * novelty + WEIGHTS["impact"] * impact + WEIGHTS["feasibility"] * feasibility


class BreakthroughEngine:
    """Generates and ranks breakthrough candidates using explicit heuristics."""

    def __init__(self, seed: Optional[int] = None):
        # A private RNG keeps generation reproducible and isolated from global
        # random state (so it never interferes with other components).
        self._rng = random.Random(seed)  # nosec B311 - idea sampling, not crypto
        self.breakthroughs: List[Breakthrough] = []

    def _draw(self, bias: float) -> float:
        """Draw a metric in [0, 1] centered near ``bias`` with bounded jitter."""
        value = bias + self._rng.uniform(-0.15, 0.15)
        return max(0.0, min(1.0, value))

    async def generate(self, domain: Optional[str] = None) -> Breakthrough:
        """Generate a single scored breakthrough candidate.

        Raises:
            ValueError: if ``domain`` is given but not a known domain.
        """
        if domain is not None and domain not in DOMAINS:
            raise ValueError(f"Unknown domain: {domain!r}. Known: {sorted(DOMAINS)}")

        chosen_domain = domain or self._rng.choice(list(DOMAINS))
        biases = DOMAINS[chosen_domain]
        method = self._rng.choice(METHODS)

        novelty = self._draw(biases["novelty"])
        impact = self._draw(biases["impact"])
        feasibility = self._draw(biases["feasibility"])
        score = _score(novelty, impact, feasibility)

        readable_domain = chosen_domain.replace("_", " ")
        bt = Breakthrough(
            id=f"bt-{len(self.breakthroughs)}",
            title=f"{method.capitalize()} for {readable_domain}",
            domain=chosen_domain,
            method=method,
            novelty=novelty,
            impact=impact,
            feasibility=feasibility,
            score=score,
            rationale=(
                f"Applies {method} to {readable_domain}: "
                f"novelty {novelty:.0%}, impact {impact:.0%}, feasibility {feasibility:.0%}."
            ),
        )
        self.breakthroughs.append(bt)
        logger.info("Generated breakthrough '%s' (score=%.3f)", bt.title, bt.score)
        return bt

    async def generate_portfolio(self, count: int = 10, domain: Optional[str] = None) -> List[Breakthrough]:
        """Generate ``count`` candidates and return them ranked by score (desc)."""
        if count < 0:
            raise ValueError("count must be non-negative")
        for _ in range(count):
            await self.generate(domain=domain)
        return self.get_top(count)

    def get_top(self, n: int = 5) -> List[Breakthrough]:
        """Return the top-``n`` generated breakthroughs by score (desc)."""
        return sorted(self.breakthroughs, key=lambda b: b.score, reverse=True)[:n]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = BreakthroughEngine(seed=42)
    portfolio = asyncio.run(engine.generate_portfolio(count=8))
    print("\nTop breakthrough candidates:")
    for i, b in enumerate(portfolio[:5], 1):
        print(f"  {i}. [{b.score:.3f}] {b.title}")
