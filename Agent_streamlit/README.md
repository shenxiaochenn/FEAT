# Forensic Agent — Streamlit UI

This project wraps your LangGraph-based forensic pipeline into a Streamlit app.
It supports two modes:

1. **Real mode** (default): Uses your actual chain modules:
   - `plan`, `abstract`, `analysis_note`, `router`, `utils`, `execute`
   Put these Python files next to `streamlit_app.py` or ensure they are importable.
2. **Demo mode** (automatic fallback): If those modules are missing, lightweight **mock chains**
   provide deterministic outputs so you can test the UI end-to-end.

## Quick start (local)

1. Create a virtual environment and install requirements:
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # (Windows: .venv\Scripts\activate)
   pip install -r requirements.txt
   ```

2. Configure secrets:
   - Copy `.streamlit/secrets.toml.tpl` to `.streamlit/secrets.toml`
   - Fill in your real keys (or leave blank to stay in demo mode).

3. Run Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```

4. Upload a `.docx` or `.txt` case file and click **Run to human feedback**.
   - Edit suggestions in the **Human feedback** box and click **Apply changes** to iterate.
   - Click **Finalize** to get candidate and final conclusions.

## Project structure

```
forensic_agent_streamlit/
├── agent_pipeline/
│   ├── __init__.py
│   ├── pipeline.py           # Your LangGraph assembly + state machine helpers
│   └── chains_mock.py        # Deterministic mock chains (fallback if your real modules are absent)
├── sample_data/
│   └── case.txt              # Example text case for demo mode
├── .streamlit/
│   └── secrets.toml.tpl      # Copy to secrets.toml and fill your keys
├── streamlit_app.py          # UI
├── requirements.txt
└── README.md
```

## Bring your own chains

If you already have modules like `plan.py`, `abstract.py`, etc., place them in the project
root (next to `streamlit_app.py`) or make them importable on `PYTHONPATH`.

The app will **try to import** your modules first and **fallback** to mocks if imports fail.

## Notes
- **Security**: Don’t hard-code API keys. Use `.streamlit/secrets.toml`.
- **Thread IDs**: Each browser session gets a unique `thread_id` to avoid collisions.
- **Output**: Use the “Download current transcript” button to save a full log as text.
