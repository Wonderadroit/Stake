from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Hypothesis:
    name: str
    evidence: list[float] = field(default_factory=list)

    @property
    def score(self) -> float:
        return sum(self.evidence)


@dataclass(frozen=True)
class DiagnosticResult:
    selected: str | None
    separation: float
    causal_depth: int
    reason: str


def diagnose(home: Hypothesis, away: Hypothesis, *, causal_depth: int, min_separation: float = 2.0) -> DiagnosticResult:
    """Apply a deliberately conservative, auditable diagnostic gate.

    This is not a probability model. It decides whether evidence separates
    competing hypotheses strongly enough to justify passing information onward.
    """
    if not 1 <= causal_depth <= 5:
        raise ValueError("causal_depth must be between 1 and 5")
    separation = abs(home.score - away.score)
    if causal_depth >= 4:
        return DiagnosticResult(None, separation, causal_depth, "causal chain too fragile")
    if separation < min_separation:
        return DiagnosticResult(None, separation, causal_depth, "insufficient hypothesis separation")
    selected = home.name if home.score > away.score else away.name
    return DiagnosticResult(selected, separation, causal_depth, "hypotheses sufficiently separated")
