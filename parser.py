from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Literal

from rapidfuzz import fuzz


@dataclass
class Field:
    aliases: tuple[str, ...]
    kind: Literal["number", "text"]
    default: float | str | None = None


@dataclass
class Group:
    alias: str
    fields: tuple[str, ...]
    count: int = -1  # -1 = all remaining numbers


@dataclass
class Config:
    fields: dict[str, Field]
    groups: dict[str, Group]
    all_aliases: list[str]


def load_config(path: Path) -> Config:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    fields = {
        name: Field(tuple(spec["aliases"]), spec["kind"], spec.get("default"))
        for name, spec in data.get("fields", {}).items()
    }
    groups = {
        name: Group(spec["alias"], tuple(spec["fields"]), spec.get("count", -1))
        for name, spec in data.get("groups", {}).items()
    }
    all_aliases = [a for f in fields.values() for a in f.aliases]
    all_aliases.extend(g.alias for g in groups.values())

    return Config(fields=fields, groups=groups, all_aliases=all_aliases)


FILLER_WORDS = frozenset(
    {
        "эм",
        "ну",
        "это",
        "вот",
        "так",
        "значит",
        "короче",
    }
)

NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")
MATCH_THRESHOLD = 80


def _normalize(text: str) -> str:
    words = text.lower().split()
    words = [w for w in words if w not in FILLER_WORDS]
    return " ".join(words)


def _find_all_matches(
    text: str, aliases: tuple[str, ...]
) -> list[tuple[float, int, int]]:
    words = text.split()
    matches: list[tuple[float, int, int]] = []

    for alias in aliases:
        alias_words = alias.split()
        alias_len = len(alias_words)

        for start in range(len(words) - alias_len + 1):
            window = " ".join(words[start : start + alias_len])
            score = fuzz.ratio(window, alias)
            if score >= MATCH_THRESHOLD:
                matches.append((score, start, start + alias_len))

    matches.sort(key=lambda m: m[0], reverse=True)
    return matches


def _find_next_alias(
    text: str, after_char_idx: int, all_aliases: list[str]
) -> int | None:
    best: int | None = None
    for alias in all_aliases:
        pos = text.find(alias, after_char_idx)
        if pos != -1 and (best is None or pos < best):
            best = pos
    return best


def _extract_after(
    config: Config,
    text: str,
    after_word_idx: int,
    kind: Literal["number", "text"],
    count: int = 1,
) -> float | list[float] | str | None:
    words = text.split()
    remaining_words = words[after_word_idx:]
    remaining = " ".join(remaining_words)

    if kind == "text":
        char_start = len(" ".join(words[:after_word_idx])) + (
            1 if after_word_idx > 0 else 0
        )
        boundary = _find_next_alias(text, char_start, config.all_aliases)
        if boundary is not None:
            extracted = text[char_start:boundary].strip()
        else:
            extracted = text[char_start:].strip()
        return extracted if extracted else None
    else:
        numbers = NUMBER_PATTERN.findall(remaining)
        if not numbers:
            return None
        floats = [float(n) for n in numbers]
        if count == 1:
            return floats[0]
        return floats[:count]


def _overlaps(span: tuple[int, int], consumed: set[int]) -> bool:
    start, end = span
    return any(i in consumed for i in range(start, end))


def parse(transcript: str, config: Config) -> dict[str, float | str]:
    normalized = _normalize(transcript)

    findings: dict[str, float | str] = {}
    consumed: set[int] = set()

    group_candidates: list[tuple[float, str, str, int, int]] = []
    for name, group in config.groups.items():
        words = normalized.split()
        alias_words = group.alias.split()
        alias_len = len(alias_words)
        for start in range(len(words) - alias_len + 1):
            window = " ".join(words[start : start + alias_len])
            score = fuzz.ratio(window, group.alias)
            if score >= MATCH_THRESHOLD:
                group_candidates.append(
                    (score, name, group.alias, start, start + alias_len)
                )
    group_candidates.sort(key=lambda c: (c[0], c[4] - c[3]), reverse=True)

    for _, name, alias, start, end in group_candidates:
        span = set(range(start, end))
        if span & consumed:
            continue
        group = config.groups[name]
        if any(f in findings for f in group.fields):
            continue
        consumed |= span
        values = _extract_after(config, normalized, end, "number", count=group.count)
        if isinstance(values, list):
            for field_name, val in zip(group.fields, values):
                findings[field_name] = val
        elif values is not None:
            findings[group.fields[0]] = values

    field_candidates: list[tuple[float, str, int, int]] = []
    for name, field in config.fields.items():
        for score, start, end in _find_all_matches(normalized, field.aliases):
            field_candidates.append((score, name, start, end))
    field_candidates.sort(key=lambda c: (c[0], c[3] - c[2]), reverse=True)

    for _, name, start, end in field_candidates:
        if _overlaps((start, end), consumed):
            continue
        consumed.update(range(start, end))
        field = config.fields[name]
        value = _extract_after(config, normalized, end, field.kind)
        if isinstance(value, list):
            raise TypeError(f"Unexpected list value for field {name}")
        if value is not None:
            findings[name] = value
        elif field.default is not None:
            findings[name] = field.default

    if not findings:
        print("Ошибка: не удалось распознать характеристики")

    for name, value in findings.items():
        print(f"{name}: {value}")

    return findings
