# medscribe

My acquaintance has a hard time finding ultrasound scribes, so I built this to make report writing easier when there's no one available.

Voice-driven medical report generator. Records dictation from a microphone, transcribes it using Whisper, extracts structured measurements via fuzzy matching, and renders a report.

## How it works

```
Audio (mic) → faster-whisper → transcript parser (RapidFuzz) → JSON + DOCX
```

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone git@github.com:dimadudin/medscribe.git

# Download the Whisper model (~500 MB)
cd medscribe
mkdir -p models
uv run python -c "
from huggingface_hub import snapshot_download
snapshot_download('Systran/faster-whisper-small', local_dir='./models/whisper-small')
"
```

## Usage

```bash
uv run main.py
```

Pick a template from the menu, then speak the measurements (e.g., "чсс 72, аорта синусы вальсальвы 34"). The report will be saved to `reports/` as both JSON and DOCX.

### GUI

```bash
uv run gui.py
```

Same pipeline with a window: pick a template, start/stop recording with a button.

## Template format

The DOCX template uses [Jinja2](https://jinja.palletsprojects.com/) placeholders for each field. The parser supports:
numeric fields, text fields, multi-value groups, computed formulas.

## Tech stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — local speech-to-text
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — fuzzy string matching for alias resolution
- [docxtpl](https://github.com/BouffardSio/docxtpl) — DOCX template rendering with Jinja2
- [sounddevice](https://python-sounddevice.readthedocs.io/) — audio recording
- [PySide6](https://wiki.qt.io/PySide6) — GUI

## Building on Windows

```powershell
uv sync
uv run pyinstaller --noconfirm --name MedScribe --windowed --collect-all faster_whisper gui.py
```

Neither models nor templates are included in the artifact:

- the Whisper model (~500 MB) is downloaded from Hugging Face on first launch
  (internet required once); a pre-downloaded `models/whisper-small` folder can
  be placed next to the exe instead;
- a `templates/` folder must be placed next to the exe.

## TODOs

- support fuzzy match accuracy dial
- tweak aliases
