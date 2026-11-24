"""Compile structured transition choreography into Wan bridge prompts (F13).

Deterministic text templates: the same choreography always yields the same
positive/negative prompt. Prompts steer the model statistically; they do not
guarantee motion, which is why prompt-only A/B comparisons keep seed, length,
size and model fixed.
"""
from __future__ import annotations

import re

from .schema import Transition

MAX_PROMPT_CHARS = 1500
DEFAULT_NEGATIVES = ("cut", "scene change", "dissolve", "crossfade", "flash", "sudden replacement",
                     "subject leaves frame", "collapsing shapes", "extra limbs", "blurry")
CAMERA = {
    "static": "The camera is static and front-facing.",
    "slow_push": "The camera pushes in slowly.",
    "slow_pull": "The camera pulls back slowly.",
    "orbit_left": "The camera orbits slowly to the left.",
    "orbit_right": "The camera orbits slowly to the right.",
    "rising": "The camera rises slowly.",
}
NOTE = "Compiled prompts are hypotheses; compare them with fixed seeds before trusting them."


class PromptError(ValueError):
    pass


def clean(text: str) -> str:
    """Drop control characters and collapse whitespace."""
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split())


def _sentence(text: str) -> str:
    text = clean(text).rstrip(" .")
    return text[:1].upper() + text[1:] + "." if text else ""


def compile_bridge_prompts(transition: Transition) -> tuple[str, str | None]:
    """(positive, negative). Without choreography: cleaned prose and no negative (graph default)."""
    base = clean(transition.prompt)
    plan = transition.choreography
    if plan is None:
        return base, None
    parts = [_sentence(base)]
    if plan.correspondences:
        pairs = "; ".join(f"{clean(c.source)} becomes {clean(c.target)}" for c in plan.correspondences)
        parts.append(f"Correspondences: {pairs}.")
    if plan.phases:
        steps = [clean(p).rstrip(" .") for p in plan.phases]
        if len(steps) == 1:
            parts.append(f"Sequence: {steps[0]}.")
        else:
            middle = "".join(f", then {s}" for s in steps[1:-1])
            parts.append(f"Sequence: first {steps[0]}{middle}, finally {steps[-1]}.")
    parts.append(CAMERA[plan.camera])
    framing = [w for w, on in (("stays centered", plan.keep_centered),
                               ("keeps the same size", plan.keep_scale)) if on]
    if framing:
        parts.append("The subject " + " and ".join(framing) + ".")
    parts.append("One continuous shot with no cuts, dissolves or crossfades.")
    positive = " ".join(p for p in parts if p)
    negatives: list[str] = []
    for term in (*DEFAULT_NEGATIVES, *plan.negative):
        term = clean(term).lower().strip(" ,")
        if term and term not in negatives:
            negatives.append(term)
    negative = ", ".join(negatives)
    for name, text in (("positive", positive), ("negative", negative)):
        if len(text) > MAX_PROMPT_CHARS:
            raise PromptError(f"compiled {name} prompt for {transition.from_anchor}->{transition.to_anchor} "
                              f"is {len(text)} characters (limit {MAX_PROMPT_CHARS})")
    return positive, negative


def variants(transition: Transition, seed: int) -> list[dict]:
    """Prompt-only A/B plan: everything but the prompt held fixed. Nothing is rendered here."""
    baseline = clean(transition.prompt)
    positive, negative = compile_bridge_prompts(transition)
    plan = [{"variant": "A-prose", "positive": baseline, "negative": None, "seed": seed}]
    if transition.choreography is not None:
        plan.append({"variant": "B-choreography", "positive": positive, "negative": negative, "seed": seed})
    return plan
