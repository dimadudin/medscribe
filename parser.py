import re

from rapidfuzz import fuzz

MEASUREMENTS: dict[str, tuple[str, ...]] = {
    "ADV": ("аорта диаметр вальсавы",),
    "ADK": ("аорта диаметр клапана",),
    "ADVS": ("аорта диаметр восходящего",),
    "DR": ("дуга размер",),
    "DNS": ("дуга нисходящего",),
    "DS": ("дуга скорость",),
    "DG": ("дуга градиент",),
}

FILLER_WORDS = frozenset(
    {
        "эм",
        "а",
    }
)

NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")
MATCH_THRESHOLD = 80


def _normalize(text: str) -> str:
    words = text.lower().split()
    words = [w for w in words if w not in FILLER_WORDS]
    return " ".join(words)


def _find_all_matches(text: str, key: str) -> list[tuple[float, int, int]]:
    words = text.split()
    matches: list[tuple[float, int, int]] = []
    aliases = MEASUREMENTS[key]

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


def _extract_number(text: str, after_word_idx: int) -> float | None:
    words = text.split()
    remaining = " ".join(words[after_word_idx:])
    match = NUMBER_PATTERN.search(remaining)
    if match:
        return float(match.group(1))
    return None


def _overlaps(span: tuple[int, int], consumed: set[int]) -> bool:
    start, end = span
    return any(i in consumed for i in range(start, end))


def parse(transcript: str) -> dict[str, float]:
    normalized = _normalize(transcript)

    candidates: list[tuple[float, str, int, int]] = []
    for name in MEASUREMENTS.keys():
        for score, start, end in _find_all_matches(normalized, name):
            candidates.append((score, name, start, end))
    candidates.sort(key=lambda c: c[0], reverse=True)

    findings: dict[str, float] = {}
    consumed: set[int] = set()

    for _, name, start, end in candidates:
        if _overlaps((start, end), consumed):
            continue

        consumed.update(range(start, end))
        value = _extract_number(normalized, end)
        if value is not None:
            findings[name] = value

    if not findings:
        print("Ошибка: не удалось распознать характеристики")

    for name, value in findings.items():
        print(f"{name}: {value}")

    return findings
