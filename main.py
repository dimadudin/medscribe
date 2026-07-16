from datetime import datetime, timezone
import json
from pathlib import Path

from docxtpl import DocxTemplate
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd

from parser import parse


MODELS_DIR = Path("models")
MODEL_NAME = "whisper-small"
MODEL_PATH = (MODELS_DIR / MODEL_NAME).as_posix()

TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "шаблон-эхо-кардиограмма.docx"
TEMPLATE_PATH = TEMPLATE_DIR / TEMPLATE_NAME

REPORTS_DIR = Path("reports")


# process mic input into a list of audio tokens (IDK I'm just making this up)
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


# output parsed measurement data into JSON and DOCX formats
def save(findings: dict[str, float]):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d.%H:%M")
    tpl_path = TEMPLATE_PATH
    reports_dir = REPORTS_DIR
    print(f"Загрузка шаблона из {tpl_path}...")

    filepath = reports_dir / f"{timestamp}.json"
    print(f"Запись протокола в {filepath}...")
    filepath.write_text(json.dumps(findings, indent=2) + "\n")

    filepath = reports_dir / f"{timestamp}.docx"
    print(f"Запись протокола в {filepath}...")
    tpl = DocxTemplate(tpl_path)
    tpl.render(findings)
    tpl.save(filepath)


def main() -> None:
    audio = record()
    transcript = transcribe(audio)
    findings = parse(transcript)
    save(findings)


if __name__ == "__main__":
    main()
