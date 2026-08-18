from dataclasses import dataclass
import re
from typing import Literal

from rapidfuzz import fuzz


@dataclass
class Field:
    aliases: tuple[str, ...]
    kind: Literal["number", "text"]
    default: float | str | None = None


FIELDS: dict[str, Field] = {
    "BSA": Field(
        (
            "бса",
            "индекс поверхности тела",
            "площадь поверхности тела",
        ),
        "number",
    ),
    "SHR": Field(
        (
            "чсс",
            "частота сердечных сокращений",
        ),
        "number",
    ),
    "H": Field(
        (
            "рост",
        ),
        "number",
    ),
    "S": Field(
        (
            "пол",
        ),
        "text",
    ),
    "Ao_Sin": Field(
        (
            "синусы вальсальвы",
            "аорта синусы вальсальвы",
            "диаметр аорты на уровне синусов вальсальвы",
        ),
        "number",
    ),
    "Ao_AV": Field(
        (
            "аортальное кольцо",
            "аорта на уровне клапана",
            "диаметр аорты на уровне аортального клапана",
        ),
        "number",
    ),
    "Ao_Asc": Field(
        (
            "восходящая",
            "аорта восходящая",
            "диаметр аорты в восходящем отделе",
        ),
        "number",
    ),
    "Ao_Arch": Field(
        (
            "дуга",
            "аорта дуга",
            "диаметр аортальной дуги",
        ),
        "number",
    ),
    "Ao_Desc": Field(
        (
            "нисходящая",
            "аорта нисходящая",
            "диаметр аорты в нисходящем отделе",
        ),
        "number",
    ),
    "Ao_Desc_V": Field(
        (
            "скорость в нисходящей",
            "аорта нисходящая скорость",
            "скорость аорты в нисходящем отделе",
        ),
        "number",
    ),
    "LA_APD": Field(
        (
            "плакс лп",
            "левое предсердие переднезадний",
            "переднезадний левого предсердия",
        ),
        "number",
    ),
    "LA_Vol": Field(
        (
            "лп объем",
            "левое предсердие объем",
            "объем левого предсердия",
        ),
        "number",
    ),
    "LV_EDV": Field(
        (
            "кдо",
            "конечно диастолический объем",
        ),
        "number",
    ),
    "LV_ESV": Field(
        (
            "ксо",
            "конечно систолический объем",
        ),
        "number",
    ),
    "IVS_B": Field(
        (
            "мжп б режим",
        ),
        "number",
    ),
    "IAS_D": Field(
        (
            "мпп",
            "межпредсердная перегородка",
        ),
        "text",
        "дефекта нет",
    ),
    "IVS_D": Field(
        (
            "мжп шунт",
            "межжелудочковая перегородка шунт",
        ),
        "text",
        "дефекта нет",
    ),
    "LV_Mass": Field(
        (
            "масса миокарда",
            "лж масса миокарда",
            "левый желудочек масса миокарда",
        ),
        "number",
    ),
    "LV_LCD": Field(
        (
            "нарушение сократимости",
        ),
        "text",
        "нет",
    ),
    "RAS": Field(
        (
            "пп площадь",
            "площадь пп",
            "правое предсердие плoщадь",
            "площадь правое предсердие",
        ),
        "number",
    ),
    "RAV": Field(
        (
            "пп объем",
            "объем пп",
            "правое предсердие объем",
            "объем правое предсердие",
        ),
        "number",
    ),
    "RVAPD": Field(
        (
            "плакс пж",
            "пж плакс",
            "пж переднезадний",
            "переднезадний пж",
        ),
        "number",
    ),
    "RVIT": Field(
        (
            "приточный тракт",
            "пж приточный тракт",
        ),
        "number",
    ),
    "RVOT": Field(
        (
            "выходной тракт пж",
            "пж выходной тракт",
        ),
        "number",
    ),
    "RVFWd": Field(
        (
            "толщина стенки",
        ),
        "number",
    ),
    "AV_LD": Field(
        (
            "аортальный клапан створки",
        ),
        "text",
        "фиброза нет",
    ),
    "AV_VEL": Field(
        (
            "аортальный клапан скорость",
        ),
        "number",
    ),
    "AV_VTI": Field(
        (
            "интеграл скорости аортального клапана",
        ),
        "number",
    ),
    "AVA": Field(
        (
            "аортальный клапан отверстие",
        ),
        "number",
    ),
    "AV_R": Field(
        (
            "аортальная регургитация",
            "регургитация на аортальном клапане",
        ),
        "text",
        "нет",
    ),
    "AV_PG": Field(
        (
            "аортальный градиент регургитации",
        ),
        "number",
    ),
    "AV_VC": Field(
        (
            "ак веноконтракта",
            "аортальный клапан веноконтракта",
        ),
        "number",
    ),
    "AV_ERO": Field(
        (
            "ак ро",
            "аортальный клапан ро",
        ),
        "number",
    ),
    "AV_AR": Field(
        (
            "ак объем регургитации",
            "аортальный клапан объем регургитации",
        ),
        "number",
    ),
    "AV_PHT": Field(
        (
            "ак полуспад давления",
            "аортальный клапан полуспад давления",
        ),
        "number",
    ),
    "AV_JET": Field(
        (
            "ширина регургитации",
        ),
        "number",
    ),
    "EDAR": Field(
        (
            "конечно диастолическая скорость аортальной регургитации",
        ),
        "number",
    ),
    "LVOT": Field(
        (
            "выходной тракт",
        ),
        "number",
    ),
    "LVOT_VEL": Field(
        (
            "выходной тракт скорость",
            "скорость на выходном тракте",
        ),
        "number",
    ),
    "LVOT_VTI": Field(
        (
            "интеграл скорости выходного тракта",
        ),
        "number",
    ),
    "MV_LD": Field(
        (
            "митральный клапан створки",
        ),
        "text",
        "фиброза нет",
    ),
    "MVA": Field(
        (
            "митральный клапан отверстие",
        ),
        "number",
    ),
    "IVRT": Field(
        (
            "вир",
        ),
        "number",
    ),
    "DT": Field(
        (
            "дт",
        ),
        "number",
    ),
    "MV_R": Field(
        (
            "митральная регургитация",
            "регургитация на митральном клапане",
        ),
        "text",
        "1 степени",
    ),
    "MR_PG": Field(
        (
            "мк градиент регургитации",
        ),
        "number",
    ),
    "MR_VC": Field(
        (
            "мк веноконтракта",
            "митральный клапан веноконтракта",
        ),
        "number",
    ),
    "MR_ERO": Field(
        (
            "мк ро",
            "митральный клапан ро",
        ),
        "number",
    ),
    "MR_VOL": Field(
        (
            "мк объем регургитации",
            "митральный клапан объем регургитации",
        ),
        "number",
    ),
    "MR_PISA": Field(
        (
            "р пиза",
            "мк радиус пиза",
            "митральный клапан радиус пиза",
        ),
        "number",
    ),
    "MV_ESEPT": Field(
        (
            "е септальная",
            "митральный клапан е септальная",
        ),
        "number",
    ),
    "MV_FD": Field(
        (
            "фиброзное кольцо",
        ),
        "number",
    ),
    "MAPSE": Field(
        (
            "мапсе",
            "мапси",
        ),
        "number",
    ),
    "PA_D": Field(
        (
            "легочная артерия",
            "легочный ствол",
        ),
        "number",
    ),
    "PA_BRANCH": Field(
        (
            "легочные ветви",
            "ветви легочной артерии",
        ),
        "number",
    ),
    "PA_EDPR": Field(
        (
            "едпр",
        ),
        "number",
    ),
    "PV_VEL": Field(
        (
            "ла скорость",
        ),
        "number",
    ),
    "PV_R": Field(
        (
            "легочная регургитация",
            "регургитация на легочной артерии",
        ),
        "text",
        "1 степени",
    ),
    "PV_AT": Field(
        (
            "ат",
        ),
        "number",
    ),
    "TV_LD": Field(
        (
            "трикус створки",
        ),
        "text",
        "фиброза нет",
    ),
    "TV_R": Field(
        (
            "трикуспидальная регургитация",
            "регургитация на трикуспидальном клапане",
        ),
        "text",
        "1 степени",
    ),
    "TR_PG": Field(
        (
            "трикус градиент регургитации",
            "трикуспидальный клапан градиент регургитации",
        ),
        "number",
    ),
    "TR_VEL": Field(
        (
            "скорость регургитации",
        ),
        "number",
    ),
    "PASP": Field(
        (
            "дла систолическое",
        ),
        "number",
    ),
    "TR_VC": Field(
        (
            "тк веноконтракта",
            "трикуспидальный клапан веноконтракта",
        ),
        "number",
    ),
    "TAPSE": Field(
        (
            "тапсе",
            "тапси",
        ),
        "number",
    ),
    "ABD": Field(
        (
            "брюшная аорта",
        ),
        "number",
    ),
    "ABD_D": Field(
        (
            "брюшная аорта особенности",
        ),
        "text",
        "поток магистральный",
    ),
    "MISC1": Field(
        (
            "особенности 1",
        ),
        "text",
    ),
    "MISC2": Field(
        (
            "особенности 2",
        ),
        "text",
    ),
    "MISC3": Field(
        (
            "особенности 3",
        ),
        "text",
    ),
}


@dataclass
class Group:
    alias: str
    fields: tuple[str, ...]
    count: int = -1  # -1 = all remaining numbers


GROUPS: dict[str, Group] = {
    "лп_4к": Group("лп 4 ac", ("LA_4C1", "LA_4C2"), 2),
    "лж_о": Group("кдр", ("LVID_d", "LVID_s"), 2),
    "мжп": Group("мжп", ("IVS_d", "IVS_s", "IVS_E"), 3),
    "зс": Group("задняя стенка", ("LVPW_d", "LVPW_s", "LVPW_E"), 3),
    "пп_4к": Group("пп 4 ac", ("RA_4C1", "RA_4C2"), 2),
    "пж_4к": Group("пж 4 ac", ("RV_4C1", "RV_4C2"), 2),
    "мк_ea": Group("митральный клапан е", ("MV_E", "MV_A"), 2),
    "мк_допплер": Group("мк тканевой допплер", ("MV_SM", "MV_ELAT", "MV_AM"), 3),
    "тк_ea": Group("трикуспидальный клапан е", ("TV_E", "TV_A"), 2),
    "тк_нпв": Group("полая", ("IVC_IN", "IVC_OUT"), 2),
    "тк_допплер": Group("тк тканевой допплер", ("TV_SM", "TV_EM", "TV_AM"), 3),
}

# Collect all alias strings for boundary detection
_ALL_ALIASES: list[str] = []
for _f in FIELDS.values():
    _ALL_ALIASES.extend(_f.aliases)
for _g in GROUPS.values():
    _ALL_ALIASES.append(_g.alias)

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


def _find_all_matches(text: str, key: str) -> list[tuple[float, int, int]]:
    words = text.split()
    matches: list[tuple[float, int, int]] = []
    aliases = FIELDS[key].aliases

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


def _find_next_alias(text: str, after_char_idx: int) -> int | None:
    best: int | None = None
    for alias in _ALL_ALIASES:
        pos = text.find(alias, after_char_idx)
        if pos != -1 and (best is None or pos < best):
            best = pos
    return best


def _extract_after(
    text: str, after_word_idx: int, kind: Literal["number", "text"], count: int = 1
) -> float | list[float] | str | None:
    words = text.split()
    remaining_words = words[after_word_idx:]
    remaining = " ".join(remaining_words)

    if kind == "text":
        char_start = len(" ".join(words[:after_word_idx])) + (
            1 if after_word_idx > 0 else 0
        )
        boundary = _find_next_alias(text, char_start)
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


def parse(transcript: str) -> dict[str, float | str]:
    normalized = _normalize(transcript)

    findings: dict[str, float | str] = {}
    consumed: set[int] = set()

    group_candidates: list[tuple[float, str, str, int, int]] = []
    for name, group in GROUPS.items():
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
        group = GROUPS[name]
        if any(f in findings for f in group.fields):
            continue
        consumed |= span
        values = _extract_after(normalized, end, "number", count=group.count)
        if isinstance(values, list):
            for field_name, val in zip(group.fields, values):
                findings[field_name] = val
        elif values is not None:
            findings[group.fields[0]] = values

    field_candidates: list[tuple[float, str, int, int]] = []
    for name, field in FIELDS.items():
        for score, start, end in _find_all_matches(normalized, name):
            field_candidates.append((score, name, start, end))
    field_candidates.sort(key=lambda c: (c[0], c[3] - c[2]), reverse=True)

    for _, name, start, end in field_candidates:
        if _overlaps((start, end), consumed):
            continue
        consumed.update(range(start, end))
        field = FIELDS[name]
        value = _extract_after(normalized, end, field.kind)
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
