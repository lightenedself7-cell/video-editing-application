"""Theme component registries and beat checking. Standard library only, so validators can import it."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]
THEMES_DIR = SKILL_DIR / "themes"
CUE_SLACK_S = 0.5  # a cue may sit this far before its beat starts (reveals lead the spoken word)


def theme_dir(theme: str) -> Path:
    return THEMES_DIR / theme


def load_registry(theme: str) -> dict | None:
    path = theme_dir(theme) / "registry.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check(spec: dict, value: Any, path: str, errors: list[str]) -> None:
    kind = spec.get("type")
    if kind == "string":
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path} must be a non-empty string")
    elif kind == "number":
        if not _num(value):
            errors.append(f"{path} must be a number")
    elif kind == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path} must be true or false")
    elif kind == "object":
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            return
        _check_fields(spec.get("fields", {}), value, path, errors)
    elif kind == "array":
        if not isinstance(value, list):
            errors.append(f"{path} must be an array")
            return
        lo, hi = spec.get("min"), spec.get("max")
        if lo is not None and len(value) < lo:
            errors.append(f"{path} needs at least {lo} item(s)")
        if hi is not None and len(value) > hi:
            errors.append(f"{path} allows at most {hi} item(s)")
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{path}[{i}] must be an object")
                continue
            _check_fields(spec.get("items", {}), item, f"{path}[{i}]", errors)
    else:
        errors.append(f"{path}: registry has unknown type {kind!r}")


def _check_fields(fields: dict, obj: dict, path: str, errors: list[str]) -> None:
    for key in obj:
        if key not in fields:
            errors.append(f"{path}.{key} is not a known prop (allowed: {', '.join(sorted(fields)) or 'none'})")
    for key, spec in fields.items():
        if key not in obj:
            if spec.get("required"):
                errors.append(f"{path}.{key} is required")
            continue
        _check(spec, obj[key], f"{path}.{key}", errors)


def _cues(value: Any, path: str):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "cue" and _num(v):
                yield f"{path}.{k}", float(v)
            else:
                yield from _cues(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _cues(v, f"{path}[{i}]")


def check_beat(registry: dict, beat: dict, prefix: str) -> list[str]:
    """Errors for one beat's `component` and `props`. A beat without a component is not checked here."""
    comp = beat.get("component")
    if comp is None:
        return []
    errors: list[str] = []
    spec = registry["components"].get(comp)
    if spec is None:
        errors.append(f"{prefix}.component {comp!r} is not in the {registry['theme']} registry (available: {', '.join(sorted(registry['components']))})")
        return errors
    if beat.get("treatment") not in spec["treatments"]:
        errors.append(f"{prefix} component {comp!r} is for {'/'.join(spec['treatments'])}, not {beat.get('treatment')!r}")
    for need in spec.get("needs", []):
        if need not in beat:
            errors.append(f"{prefix} component {comp!r} needs the beat field {need!r}")
    props = beat.get("props", {})
    if not isinstance(props, dict):
        errors.append(f"{prefix}.props must be an object")
        return errors
    _check_fields(spec["props"], props, f"{prefix}.props", errors)
    start, end = beat.get("start"), beat.get("end")
    if _num(start) and _num(end):
        for path, cue in _cues(props, f"{prefix}.props"):
            if not (start - CUE_SLACK_S <= cue <= end):
                errors.append(f"{path} = {cue} is outside the beat ({start}-{end})")
    return errors
