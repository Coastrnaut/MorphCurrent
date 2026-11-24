"""Creative brief → editable storyboard (F22). Deterministic templates, no network, no GPU.

A brief lists ordered scenes (subject, optional details, optional morph hint), a target
duration, tempo and style pack. The planner writes a schema-valid storyboard: the first
anchor by text-to-image, the rest by reference edit of the previous anchor, transitions
with F13 choreography, and beat budgets that hit the target duration using valid Wan
4n+1 lengths. Prompts are starting points for human editing; nothing is rendered.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .timeline import derived_seed, frame_count_for_beats

MAX_TEXT = 200


class BriefError(ValueError):
    pass


def _clean(text: str) -> str:
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split())


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=1, max_length=MAX_TEXT)
    details: str | None = Field(default=None, max_length=400)
    morph: str | None = Field(default=None, max_length=MAX_TEXT,
                              description="how this subject physically turns into the next")

    @field_validator("subject", "details", "morph")
    @classmethod
    def clean(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean(value)
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class Brief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,79}$")
    scenes: list[Scene] = Field(min_length=2, max_length=200)
    duration_s: float = Field(gt=0, le=3600)
    bpm: float = Field(default=120, gt=0, le=400)
    style_pack: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    style_description: str = "Cinematic, consistent lighting and composition."
    width: int = 832
    height: int = 480
    fps: int = 16
    max_bridge_frames: int = 81
    seed: int = Field(default=0, ge=0)
    # Provenance note for Claude Desktop pre-drafting (F22 US3); header only, never in the plan hash
    drafted_by: str | None = Field(default=None, max_length=120)


def _slug(text: str, used: set[str]) -> str:
    words = [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]
    while words and words[0] in {"a", "an", "the"}:
        words = words[1:]
    base = ""
    for w in words:  # whole words, at most 24 characters
        if len(base) + len(w) + (1 if base else 0) > 24:
            break
        base = f"{base}-{w}" if base else w
    base = base or (words[0][:24] if words else "scene")
    if not base[0].isalpha():
        base = "s-" + base
    name, n = base, 2
    while name in used:
        name, n = f"{base}-{n}", n + 1
    used.add(name)
    return name


def plan_storyboard(brief: Brief) -> tuple[dict, dict]:
    """Return (storyboard dict, preview dict)."""
    n = len(brief.scenes) - 1
    beats_each = brief.duration_s / n * brief.bpm / 60.0
    try:
        frames = frame_count_for_beats(beats_each, brief.bpm, brief.fps, brief.max_bridge_frames)
    except ValueError as exc:
        span_max = (brief.max_bridge_frames - 1) / brief.fps
        raise BriefError(f"{brief.duration_s} s over {n} transitions does not fit Wan lengths "
                         f"(5..{brief.max_bridge_frames} frames, at most {span_max:.2f} s each): {exc}. "
                         "Add scenes, shorten the duration or split transitions (ladder-propose).") from exc
    span = n * (frames - 1) / brief.fps
    if abs(span - brief.duration_s) > (frames - 1) / brief.fps:
        minimum = n * 4 / brief.fps
        raise BriefError(f"{brief.duration_s} s cannot be reached with {n} transitions: the shortest Wan "
                         f"bridge is 5 frames, so the minimum is {minimum:.2f} s (got {span:.2f} s)")
    used: set[str] = set()
    ids = [_slug(s.subject, used) for s in brief.scenes]
    anchors = []
    for k, (scene, aid) in enumerate(zip(brief.scenes, ids)):
        desc = scene.subject + (f", {scene.details}" if scene.details else "")
        if k == 0:
            anchors.append({"id": aid, "prompt": f"{desc[0].upper()}{desc[1:]}.", "seed": derived_seed(brief.seed, f"anchor:{aid}"),
                            "generation": "text_to_image"})
        else:
            anchors.append({"id": aid, "prompt": f"Transform the subject into {desc}; keep the same framing, "
                                                 f"scale, background and lighting.",
                            "seed": derived_seed(brief.seed, f"anchor:{aid}"),
                            "generation": "reference_edit", "reference": ids[k - 1]})
    transitions = []
    for k in range(n):
        a, b = brief.scenes[k], brief.scenes[k + 1]
        hint = a.morph or f"the {a.subject} reshapes into the {b.subject}"
        transitions.append({
            "from": ids[k], "to": ids[k + 1], "duration_beats": round(beats_each, 6),
            "seed": derived_seed(brief.seed, f"bridge:{ids[k]}->{ids[k + 1]}"),
            "motion": "static", "mode": "direct",
            "prompt": f"Continuous physical metamorphosis in one shot: {hint}.",
            "choreography": {"correspondences": [{"source": a.subject, "target": b.subject}],
                             "camera": "static", "keep_centered": True, "keep_scale": True},
        })
    style = {"description": brief.style_description}
    if brief.style_pack:
        style["pack"] = brief.style_pack
    storyboard = {
        "schema_version": 1, "name": brief.title.strip().replace(" ", "-").lower(),
        "render": {"width": brief.width, "height": brief.height, "generation_fps": brief.fps,
                   "delivery_fps": 24, "anchor_profile": "anchor_t2i", "bridge_profile": "wan22_flf2v",
                   "master_seed": brief.seed, "max_bridge_frames": brief.max_bridge_frames},
        "style": style,
        "audio": {"bpm": brief.bpm, "synchronization": "none", "beat_offset_seconds": 0},
        "anchors": anchors, "transitions": transitions,
    }
    span = n * (frames - 1) / brief.fps
    preview = {"scenes": ids, "transitions": n, "frames_per_bridge": frames,
               "seconds_per_bridge": round((frames - 1) / brief.fps, 4),
               "anchor_span_s": round(span, 3), "target_s": brief.duration_s,
               "residual_s": round(span - brief.duration_s, 3),
               "unique_frames": 1 + n * (frames - 1)}
    return storyboard, preview


# --- F22 US3: local checks for Claude-Desktop-drafted briefs and storyboards ------------------------

FORBIDDEN = [  # creative text must never choose models, files, nodes or workflow internals
    (re.compile(r"https?://|\bwww\.", re.I), "url"),
    (re.compile(r"\.(safetensors|ckpt|gguf|pt|pth|bin)\b", re.I), "model file (safetensors/ckpt/...)"),
    (re.compile(r"\blora\b|\blycoris\b", re.I), "lora"),
    (re.compile(r"\bk?sampler\b|\bcomfy ?ui\b|\bworkflow\b|\bnode\s*(id|#)?\s*\d+|\bvae\b|\bunet\b|"
                r"\bclip ?text ?encode\b|\bcfg\b|\bdenoise\b", re.I), "comfyui/workflow internals (ksampler, node, workflow ...)"),
    (re.compile(r"\bqwen\b|\bwan ?2(\.\d)?\b|\bsdxl\b|\bstable diffusion\b|\bmidjourney\b|\bdall-?e\b|"
                r"\bcheckpoint\b", re.I), "model name/checkpoint"),
]
LONG_PROMPT = 600


def _texts(data: dict, kind: str):
    """(field path, text) pairs of creative text in a brief or storyboard mapping."""
    if kind == "brief":
        yield "title", data.get("title")
        yield "style_description", data.get("style_description")
        for i, s in enumerate(data.get("scenes") or []):
            for key in ("subject", "details", "morph"):
                yield f"scenes[{i}].{key}", (s or {}).get(key)
        return
    yield "style.description", (data.get("style") or {}).get("description")
    for i, a in enumerate(data.get("anchors") or []):
        for key in ("prompt", "negative_prompt"):
            yield f"anchors[{i}].{key}", (a or {}).get(key)
    for i, tr in enumerate(data.get("transitions") or []):
        yield f"transitions[{i}].prompt", (tr or {}).get("prompt")
        ch = (tr or {}).get("choreography") or {}
        for j, c in enumerate(ch.get("correspondences") or []):
            yield f"transitions[{i}].choreography.correspondences[{j}]", f"{c.get('source', '')} {c.get('target', '')}"
        for j, ph in enumerate(ch.get("phases") or []):
            yield f"transitions[{i}].choreography.phases[{j}]", ph
        for j, ng in enumerate(ch.get("negative") or []):
            yield f"transitions[{i}].choreography.negative[{j}]", ng


def lint_draft(data: object, repo_root: str = ".") -> dict:
    """Validate a drafted brief or storyboard (as a YAML mapping). Errors block; warnings advise."""
    from .dag import compile_plan
    from .schema import Storyboard
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {"kind": "unknown", "errors": ["schema: draft must be a YAML mapping"], "warnings": []}
    kind = "storyboard" if "schema_version" in data else "brief"
    for path, text in _texts(data, kind):
        if not isinstance(text, str):
            continue
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                errors.append(f"{path}: contains {label}: {pattern.search(text).group(0)!r}")
        if path.endswith(".prompt") and len(text) > LONG_PROMPT:
            warnings.append(f"{path}: prompt is {len(text)} characters (over {LONG_PROMPT}); consider trimming")
    report: dict = {"kind": kind}
    try:
        if kind == "brief":
            storyboard, preview = plan_storyboard(Brief.model_validate(data))
            report.update(bridges=preview["transitions"], frames_per_bridge=preview["frames_per_bridge"],
                          anchor_span_s=preview["anchor_span_s"])
            sb = Storyboard.model_validate(storyboard)
        else:
            sb = Storyboard.model_validate(data)
        plan = compile_plan(sb, repo_root=repo_root)
        bridges = [t for t in plan["tasks"].values() if t["kind"] == "bridge"]
        report.update(bridges=len(bridges), plan_sha256=plan["plan_sha256"],
                      duration_s=plan["tasks"]["final:movie"]["nominal_duration_seconds"],
                      blocked=plan["blocked"])
        for anchor in sb.anchors:
            if anchor.generation == "independent_t2i":
                warnings.append(f"anchor {anchor.id}: independent_t2i breaks reference-edit lineage "
                                "(explicit fallback; prefer reference_edit)")
        for tr in sb.transitions:
            if not (tr.choreography and tr.choreography.correspondences):
                warnings.append(f"transition {tr.from_anchor}->{tr.to_anchor}: no choreography correspondences "
                                "(physical part-to-part mapping helps Wan morph)")
    except (ValueError, BriefError) as exc:  # pydantic ValidationError is a ValueError
        errors.insert(0, f"schema: {str(exc).splitlines()[0]}" + (f" ({len(str(exc).splitlines())} lines)"
                                                                 if len(str(exc).splitlines()) > 1 else ""))
    return {**report, "errors": errors, "warnings": warnings}
