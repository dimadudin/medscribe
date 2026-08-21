# medscribe

Voice-driven medical report generator. Records dictation from a microphone, transcribes it using Whisper, extracts structured measurements via fuzzy matching, and renders a formatted DOCX report.

## How it works

```
Audio (mic) → faster-whisper (RU) → transcript parser (RapidFuzz) → JSON + DOCX
```

1. Records audio from the default microphone until Enter is pressed
2. Transcribes the recording to text using a local Whisper model (Russian)
3. Parses the transcript to extract medical measurements using fuzzy alias matching
4. Saves results as JSON and renders a formatted DOCX report from a Jinja2 template

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Microphone access

## Setup

```bash
git clone git@github.com:dimadudin/medscribe.git
cd medscribe

# Create directories
mkdir -p models reports templates

# Download the Whisper model (~500 MB)
uv run python -c "
from huggingface_hub import snapshot_download
snapshot_download('Systran/faster-whisper-small', local_dir='./models/whisper-small')
"
```

Place your DOCX template with Jinja2 placeholders in `templates/`.

## Usage

```bash
uv run main.py
```

The tool will start recording audio. Speak the measurements in Russian (e.g., "чсс 72, аорта синусы вальсальвы 34"). Press Enter when done. The report will be saved to `reports/` as both JSON and DOCX.

## Template format

The DOCX template uses [Jinja2](https://jinja.palletsprojects.com/) placeholders for each field. The parser supports:

- **Numeric fields** — measurements like heart rate, chamber diameters, ejection fraction
- **Text fields** — categorical values like sex, defect presence
- **Multi-value groups** — repeated measurements (e.g., mitral valve E/A ratios)
- **Russian voice aliases** — each field can have multiple spoken forms (e.g., "чсс" / "частота сердечных сокращений")
- **Computed formulas** — the template can include Jinja2 expressions for derived values (e.g., LV mass, pressure gradients)
- **Conditional conclusions** — `{% if %}` blocks for automatic assessment (e.g., "LA dilated if volume/BSA > 34")

## Tech stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — local speech-to-text
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — fuzzy string matching for alias resolution
- [docxtpl](https://github.com/BouffardSio/docxtpl) — DOCX template rendering with Jinja2
- [sounddevice](https://python-sounddevice.readthedocs.io/) — audio recording
