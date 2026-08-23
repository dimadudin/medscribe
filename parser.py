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
    aliases: tuple[str, ...]
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
    groups = {}
    for name, spec in data.get("groups", {}).items():
        aliases = spec["aliases"] if "aliases" in spec else [spec["alias"]]
        groups[name] = Group(
            tuple(aliases),
            tuple(spec["fields"]),
            spec.get("count", -1),
        )
    all_aliases = [a for f in fields.values() for a in f.aliases]
    all_aliases.extend(a for g in groups.values() for a in g.aliases)

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

NUMBER_PATTERN = re.compile(r"(\d+(?:[.,]\d+)*)")
MATCH_THRESHOLD = 80


def _token_variants(token: str) -> list[list[float]]:
    parts = token.split(",")
    if len(parts) == 1:
        return [[float(token)]]

    merge_first = parts[0] == "0" or (len(parts) == 2 and len(parts[-1]) == 1)

    def step(
        i: int, acc: list[float]
    ) -> tuple[tuple[int, list[float]] | None, tuple[int, list[float]] | None]:
        merged: tuple[int, list[float]] | None = None
        separated: tuple[int, list[float]] | None = None
        if i + 1 < len(parts) and parts[i + 1] != "0":
            merged = (i + 2, acc + [float(f"{parts[i]}.{parts[i + 1]}")])
        if parts[i] != "0":
            separated = (i + 1, acc + [float(parts[i])])
        return merged, separated

    variants: list[list[float]] = []
    stack = [(0, [])]
    while stack:
        i, acc = stack.pop()
        if i == len(parts):
            variants.append(acc)
            continue
        merged, separated = step(i, acc)
        if merge_first:
            branches = [b for b in (merged, separated) if b]
        else:
            branches = [b for b in (separated, merged) if b]
        stack.extend(reversed(branches))

    return variants


def _select_numbers(tokens: list[str], count: int) -> list[float]:
    option_lists = [_token_variants(t) for t in tokens]

    if count > 1:
        found: list[float] | None = None

        def dfs(i: int, acc: list[float]) -> None:
            nonlocal found
            if found is not None or len(acc) > count:
                return
            if len(acc) == count:
                found = acc.copy()
                return
            if i == len(option_lists):
                return
            for variant in option_lists[i]:
                dfs(i + 1, acc + variant)
                if found is not None:
                    return

        dfs(0, [])
        if found is not None:
            return found

    out: list[float] = []
    for options in option_lists:
        out.extend(options[0])
    return out


def _normalize(text: str) -> str:
    words = text.lower().split()
    words = [w for w in words if w not in FILLER_WORDS]
    return " ".join(words)


NUMERIC_TOKEN = re.compile(r"\d+(?:[.,]\d+)*")


def _is_numeric_token(token: str) -> bool:
    return NUMERIC_TOKEN.fullmatch(token.strip(".,;:")) is not None


def _tokens_compatible(alias_words: list[str], window_words: list[str]) -> bool:
    return all(
        _is_numeric_token(a) == _is_numeric_token(w)
        for a, w in zip(alias_words, window_words)
    )


def _find_all_matches(
    text: str, aliases: tuple[str, ...]
) -> list[tuple[float, int, int]]:
    words = text.split()
    matches: list[tuple[float, int, int]] = []

    for alias in aliases:
        alias_words = alias.split()
        alias_len = len(alias_words)

        for start in range(len(words) - alias_len + 1):
            window_words = words[start : start + alias_len]
            if not _tokens_compatible(alias_words, window_words):
                continue
            window = " ".join(window_words)
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
    hard_stop: int | None = None,
) -> float | list[float] | str | None:
    words = text.split()
    remaining_words = words[after_word_idx:]
    remaining = " ".join(remaining_words)

    if kind == "text":
        char_start = len(" ".join(words[:after_word_idx])) + (
            1 if after_word_idx > 0 else 0
        )
        boundary = _find_next_alias(text, char_start, config.all_aliases)
        if hard_stop is not None and (boundary is None or hard_stop < boundary):
            boundary = hard_stop
        strip_chars = ' \t\n.,;:"«»'
        if boundary is not None:
            extracted = text[char_start:boundary].strip(strip_chars)
        else:
            extracted = text[char_start:].strip(strip_chars)
        return extracted if extracted else None
    else:
        tokens = NUMBER_PATTERN.findall(remaining)
        if not tokens:
            return None
        floats = _select_numbers(tokens, count)
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
    attempted_groups: set[str] = set()
    attempted_fields: set[str] = set()

    group_candidates: list[tuple[float, str, str, int, int]] = []
    for name, group in config.groups.items():
        words = normalized.split()
        for alias in group.aliases:
            alias_words = alias.split()
            alias_len = len(alias_words)
            for start in range(len(words) - alias_len + 1):
                window_words = words[start : start + alias_len]
                if not _tokens_compatible(alias_words, window_words):
                    continue
                window = " ".join(window_words)
                score = fuzz.ratio(window, alias)
                if score >= MATCH_THRESHOLD:
                    group_candidates.append(
                        (score, name, alias, start, start + alias_len)
                    )
    group_candidates.sort(key=lambda c: (c[0], c[4] - c[3]), reverse=True)
    group_spans: list[tuple[int, int]] = []

    for _, name, alias, start, end in group_candidates:
        span = set(range(start, end))
        if span & consumed:
            continue
        group = config.groups[name]
        if name in attempted_groups or any(f in findings for f in group.fields):
            continue
        attempted_groups.add(name)
        consumed |= span
        group_spans.append((start, end))
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

    words = normalized.split()
    word_starts: list[int] = []
    pos = 0
    for w in words:
        word_starts.append(pos)
        pos += len(w) + 1
    all_spans = group_spans + [(s, e) for _, _, s, e in field_candidates]

    for _, name, start, end in field_candidates:
        if name in attempted_fields or _overlaps((start, end), consumed):
            continue
        attempted_fields.add(name)
        consumed.update(range(start, end))
        consumed.update(range(start, end))
        field = config.fields[name]
        hard_stop = None
        if field.kind == "text":
            stops = [s for s, _ in all_spans if s >= end]
            if stops:
                hard_stop = word_starts[min(stops)]
        value = _extract_after(config, normalized, end, field.kind, hard_stop=hard_stop)
        if isinstance(value, list):
            raise TypeError(f"Unexpected list value for field {name}")
        if value is not None:
            findings[name] = value
        elif field.default is not None:
            findings[name] = field.default

    if not findings:
        raise ValueError("Ошибка: не удалось распознать характеристики")

    for name, value in findings.items():
        print(f"{name}: {value}")

    return findings
