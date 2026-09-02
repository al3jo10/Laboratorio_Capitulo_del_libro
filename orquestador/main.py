"""
Orquestador del pipeline conversacional local para agentes en RV.
Cadena serial (versión A / línea base): STT -> LLM -> TTS
Instrumentado por etapa para caracterización del presupuesto de latencia.
"""

import os
import csv
import time
import uuid
import wave
import contextlib
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

import requests  # type: ignore[import-not-found]
from fastapi import FastAPI, File, UploadFile, HTTPException  # type: ignore[import-not-found]
from fastapi.responses import FileResponse, JSONResponse  # type: ignore[import-not-found]
try:
    from faster_whisper import WhisperModel  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None

# ----------------------------- Configuración -----------------------------

OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE= os.getenv("WHISPER_COMPUTE", "int8")
PIPER_VOICE    = os.getenv("PIPER_VOICE", "/voices/es_ES-davefx-medium.onnx")
MAX_TOKENS     = int(os.getenv("MAX_TOKENS", "60"))

CSV_PATH   = Path("/mediciones/latencias.csv")
AUDIO_DIR  = Path("/mediciones/audio_salida")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "Eres un personaje no jugable dentro de un entorno de realidad virtual. "
    "Respondes de forma breve y natural, en español, en un máximo de dos frases. "
    "No uses listas, emojis ni formato markdown."
)

CAMPOS = [
    "id", "timestamp", "modelo_llm", "modelo_whisper", "dispositivo_whisper",
    "dur_audio_entrada_s", "n_caracteres_transcripcion", "n_tokens_respuesta",
    "ms_stt", "ms_llm", "ms_tts", "ms_io", "ms_total", "ms_primer_fonema",
    "transcripcion", "respuesta",
]

app = FastAPI(title="Orquestador VR - Agente Local")

# Carga única del modelo STT al arranque (evita recarga por petición).
if WhisperModel is not None:
    whisper = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
else:
    whisper = None


# ----------------------------- Utilidades -----------------------------

@contextmanager
def etapa(registro: dict, nombre: str):
    """Mide el tiempo de una etapa y lo escribe en ms en el registro."""
    t0 = time.perf_counter()
    yield
    registro[nombre] = round((time.perf_counter() - t0) * 1000, 2)


def duracion_wav(path: str) -> float:
    try:
        with contextlib.closing(wave.open(path, "rb")) as f:
            return round(f.getnframes() / float(f.getframerate()), 3)
    except Exception:
        return -1.0


def escribir_fila(registro: dict) -> None:
    nuevo = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        if nuevo:
            w.writeheader()
        w.writerow(registro)


# ----------------------------- Endpoints -----------------------------

@app.get("/ping")
def health_check():
    return {
        "status": "ok",
        "modelo_llm": OLLAMA_MODEL,
        "modelo_stt": WHISPER_MODEL,
        "stt_lib_loaded": WhisperModel is not None,
    }


@app.post("/conversar")
async def conversar(audio: UploadFile = File(...)):
    """Recibe un wav, devuelve la respuesta hablada del agente."""
    reg = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modelo_llm": OLLAMA_MODEL,
        "modelo_whisper": WHISPER_MODEL,
        "dispositivo_whisper": WHISPER_DEVICE,
    }
    t_inicio = time.perf_counter()

    # --- I/O de entrada ---
    with etapa(reg, "ms_io"):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(await audio.read())
            ruta_entrada = tmp.name
    reg["dur_audio_entrada_s"] = duracion_wav(ruta_entrada)

    try:
        # --- STT ---
        if whisper is None:
            raise HTTPException(status_code=500, detail="Dependencia 'faster_whisper' no disponible en el entorno.")
        with etapa(reg, "ms_stt"):
            segmentos, _ = whisper.transcribe(ruta_entrada, language="es", beam_size=1)
            transcripcion = " ".join(s.text for s in segmentos).strip()
        reg["transcripcion"] = transcripcion
        reg["n_caracteres_transcripcion"] = len(transcripcion)

        if not transcripcion:
            raise HTTPException(status_code=422, detail="No se detectó habla en el audio.")

        # --- LLM ---
        with etapa(reg, "ms_llm"):
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": transcripcion},
                    ],
                    "stream": False,
                    "options": {"num_predict": MAX_TOKENS, "temperature": 0.7},
                },
                timeout=120,
            )
            r.raise_for_status()
            datos = r.json()
            respuesta = datos["message"]["content"].strip()
        reg["respuesta"] = respuesta
        reg["n_tokens_respuesta"] = datos.get("eval_count", -1)

        # --- TTS ---
        ruta_salida = AUDIO_DIR / f"{reg['id']}.wav"
        with etapa(reg, "ms_tts"):
            proc = subprocess.run(
                ["piper", "--model", PIPER_VOICE, "--output_file", str(ruta_salida)],
                input=respuesta.encode("utf-8"),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Fallo en TTS: {proc.stderr.decode('utf-8', 'ignore')[:300]}",
                )

        reg["ms_total"] = round((time.perf_counter() - t_inicio) * 1000, 2)
        # En la versión serial el audio solo suena cuando todo terminó.
        reg["ms_primer_fonema"] = reg["ms_total"]
        escribir_fila(reg)

        return FileResponse(
            ruta_salida,
            media_type="audio/wav",
            headers={
                "X-Id": reg["id"],
                "X-Transcripcion": transcripcion[:200],
                "X-Respuesta": respuesta[:200],
                "X-Ms-Total": str(reg["ms_total"]),
                "X-Ms-Stt": str(reg["ms_stt"]),
                "X-Ms-Llm": str(reg["ms_llm"]),
                "X-Ms-Tts": str(reg["ms_tts"]),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "id": reg["id"]})
    finally:
        os.unlink(ruta_entrada)