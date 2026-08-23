from datetime import datetime, timezone
import json
from pathlib import Path

from docxtpl import DocxTemplate
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd


MODELS_DIR = Path("models")
MODEL_NAME = "whisper-small"
MODEL_PATH = (MODELS_DIR / MODEL_NAME).as_posix()

TEMPLATES_DIR = Path("templates")
REPORTS_DIR = Path("reports")


class Recorder:
    def __init__(self, samplerate: int = 16000):
        self._samplerate = samplerate
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        self._frames = []

        def callback(indata, frame_count, time_info, status):
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self._samplerate,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is None:
            raise RuntimeError("Ошибка: запись не была запущена")
        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._frames:
            raise RuntimeError("Ошибка: не удалось распознать аудио")

        return np.concatenate(self._frames, axis=0).flatten()


class Transcriber:
    def __init__(
        self,
        model_path: str = MODEL_PATH,
        device: str = "auto",
        compute_type: str = "int8",
    ):
        self._model_path = model_path
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    def transcribe(self, audio: np.ndarray) -> str:
        if self._model is None:
            print(f"Загрузка модели из {self._model_path}...")
            self._model = WhisperModel(
                self._model_path,
                device=self._device,
                compute_type=self._compute_type,
            )
        print("Транскрипция...")
        segments, _ = self._model.transcribe(
            audio,
            language="ru",
            beam_size=5,
            vad_filter=True,
        )
        transcript = " ".join(segment.text for segment in segments).strip()
        print(f'Текст: "{transcript}"')
        return transcript


def discover_templates() -> dict[str, Path]:
    templates = {
        d.name: d
        for d in sorted(TEMPLATES_DIR.iterdir())
        if d.is_dir()
        and (d / "fields.toml").is_file()
        and (d / "template.docx").is_file()
    }
    if not templates:
        raise RuntimeError(f"Ошибка: не найдено ни одного шаблона в {TEMPLATES_DIR}/")
    return templates


def save(
    findings: dict[str, float | str],
    bundle_dir: Path,
    reports_dir: Path = REPORTS_DIR,
) -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d.%H_%M")
    tpl_path = bundle_dir / "template.docx"
    print(f"Загрузка шаблона из {tpl_path}...")
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"{timestamp}.json"
    print(f"Запись протокола в {json_path}...")
    json_path.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n")

    docx_path = reports_dir / f"{timestamp}.docx"
    print(f"Запись протокола в {docx_path}...")
    tpl = DocxTemplate(tpl_path)
    tpl.render(findings)
    tpl.save(docx_path)

    return json_path, docx_path
