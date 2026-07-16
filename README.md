# Idk whatever

Create dirs i guess

```bash
mkdir models
mkdir reports
```

Get a model

```bash
uv run python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small', local_dir='./models/whisper-small')"
```

Run it

```bash
uv run main.py
```
