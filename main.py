from pathlib import Path

from pipeline import Recorder, Transcriber, discover_templates, save
from parser import load_config, parse


def select_template(templates: dict[str, Path]) -> Path:
    print("Доступные шаблоны:")
    for i, name in enumerate(templates, 1):
        print(f"  {i}) {name}")

    while True:
        choice = input("Выберите номер: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(templates):
            return templates[list(templates)[int(choice) - 1]]
        print(f"Ошибка: введите число от 1 до {len(templates)}")


def main() -> None:
    template_dir = select_template(discover_templates())
    config = load_config(template_dir / "fields.toml")

    recorder = Recorder()
    print("Запись... нажмите Enter, чтобы остановить")
    recorder.start()
    input()
    audio = recorder.stop()

    transcript = Transcriber().transcribe(audio)
    findings = parse(transcript, config)
    save(findings, template_dir)


if __name__ == "__main__":
    main()
