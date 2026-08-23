import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pipeline import Recorder, Transcriber, discover_templates, save
from parser import load_config, parse


class WorkerSignals(QObject):
    status = Signal(str)
    transcript = Signal(str)
    done = Signal(str)
    error = Signal(str)


class MedScribeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedScribe")

        self._signals = WorkerSignals()

        self._recorder = Recorder()
        self._transcriber = Transcriber()
        self._templates = discover_templates()
        self._template_dir: Path | None = None
        self._state = "idle"
        self._record_started_at = 0.0

        self._combo = QComboBox()
        self._combo.addItems(list(self._templates))

        self._button = QPushButton()
        self._button.clicked.connect(self._on_button)

        self._status_label = QLabel()

        self._transcript_view = QTextEdit()
        self._transcript_view.setReadOnly(True)
        self._transcript_view.setFixedHeight(80)

        self._signals.status.connect(self._status_label.setText)
        self._signals.transcript.connect(self._transcript_view.setPlainText)
        self._signals.done.connect(self._on_done)
        self._signals.error.connect(self._on_error)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Шаблон:"))
        layout.addWidget(self._combo)
        layout.addWidget(self._button)
        layout.addWidget(self._status_label)
        layout.addWidget(QLabel("Распознанный текст:"))
        layout.addWidget(self._transcript_view)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._tick)

        self._set_state("idle")

    def _set_state(self, state: str) -> None:
        self._state = state
        if state == "idle":
            self._button.setText("Начать запись")
            self._button.setEnabled(True)
            self._combo.setEnabled(True)
        elif state == "recording":
            self._button.setText("Остановить запись")
            self._button.setEnabled(True)
            self._combo.setEnabled(False)
        else:
            self._button.setText("Обработка...")
            self._button.setEnabled(False)
            self._combo.setEnabled(False)

    def _on_button(self) -> None:
        if self._state == "idle":
            self._template_dir = Path(self._templates[self._combo.currentText()])
            self._transcript_view.clear()
            try:
                self._recorder.start()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
                return
            self._record_started_at = time.monotonic()
            self._set_state("recording")
            self._timer.start()
            self._tick()
        elif self._state == "recording":
            self._timer.stop()
            try:
                audio = self._recorder.stop()
            except Exception as e:
                self._set_state("idle")
                self._status_label.setText("Готово к новой записи")
                QMessageBox.critical(self, "Ошибка", str(e))
                return
            self._set_state("processing")
            threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _tick(self) -> None:
        if self._state != "recording":
            return
        elapsed = int(time.monotonic() - self._record_started_at)
        self._status_label.setText(f"Запись... {elapsed} с")

    def _process(self, audio) -> None:
        try:
            assert self._template_dir is not None
            self._signals.status.emit("Транскрипция...")
            transcript = self._transcriber.transcribe(audio)
            self._signals.transcript.emit(transcript)
            config = load_config(self._template_dir / "fields.toml")
            findings = parse(transcript, config)
            self._signals.status.emit("Сохранение...")
            json_path, docx_path = save(
                findings, self._template_dir, transcript=transcript
            )
            self._signals.done.emit(f"Готово:\n{json_path}\n{docx_path}")
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_done(self, text: str) -> None:
        self._set_state("idle")
        self._status_label.setText(text)

    def _on_error(self, message: str) -> None:
        self._set_state("idle")
        self._status_label.setText("Готово к новой записи")
        QMessageBox.critical(self, "Ошибка", message)


def main() -> None:
    app = QApplication(sys.argv)
    window = MedScribeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
