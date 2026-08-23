from datetime import datetime, timezone
import json
from pathlib import Path

from docxtpl import DocxTemplate
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd

from parser import load_config, parse


MODELS_DIR = Path("models")
MODEL_NAME = "whisper-small"
MODEL_PATH = (MODELS_DIR / MODEL_NAME).as_posix()

REPORT_TYPES_DIR = Path("report_types")
REPORTS_DIR = Path("reports")


def record(samplerate: int = 16000) -> np.ndarray:
    print("Запись... нажмите Enter, чтобы остановить")
    frames: list[np.ndarray] = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=samplerate, channels=1, dtype="float32", callback=callback
    ):
        input()

    if not frames:
        raise RuntimeError("Ошибка: не удалось распознать аудио")

    return np.concatenate(frames, axis=0).flatten()


# process audio tokens into a string
def transcribe(audio: np.ndarray) -> str:
    print(f"Загрузка модели из {MODEL_PATH}...")
    model = WhisperModel(MODEL_PATH, device="auto", compute_type="default")
    print("Транскрипция...")
    segments, _ = model.transcribe(
        audio,
        language="ru",
        beam_size=5,
        vad_filter=True,
    )
    transcript = " ".join(segment.text for segment in segments).strip()
    print(f'Текст: "{transcript}"')
    return transcript


def discover_report_types() -> dict[str, Path]:
    bundles = {
        d.name: d
        for d in sorted(REPORT_TYPES_DIR.iterdir())
        if d.is_dir()
        and (d / "fields.toml").is_file()
        and (d / "template.docx").is_file()
    }
    if not bundles:
        raise RuntimeError(
            f"Ошибка: не найдено ни одного типа отчётов в {REPORT_TYPES_DIR}/"
        )
    return bundles


def select_report_type(bundles: dict[str, Path]) -> Path:
    print("Доступные типы отчётов:")
    for i, name in enumerate(bundles, 1):
        print(f"  {i}) {name}")

    while True:
        choice = input("Выберите номер: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(bundles):
            return bundles[list(bundles)[int(choice) - 1]]
        print(f"Ошибка: введите число от 1 до {len(bundles)}")


# output parsed measurement data into JSON and DOCX formats
def save(findings: dict[str, float | str], bundle_dir: Path):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d.%H_%M")
    tpl_path = bundle_dir / "template.docx"
    print(f"Загрузка шаблона из {tpl_path}...")
    REPORTS_DIR.mkdir(exist_ok=True)

    filepath = REPORTS_DIR / f"{timestamp}.json"
    print(f"Запись протокола в {filepath}...")
    filepath.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n")

    filepath = REPORTS_DIR / f"{timestamp}.docx"
    print(f"Запись протокола в {filepath}...")
    tpl = DocxTemplate(tpl_path)
    tpl.render(findings)
    tpl.save(filepath)


def main() -> None:
    bundle_dir = select_report_type(discover_report_types())
    config = load_config(bundle_dir / "fields.toml")
    audio = record()
    transcript = transcribe(audio)
    findings = parse(transcript, config)
    save(findings, bundle_dir)


if __name__ == "__main__":
    main()
