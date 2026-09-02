"""
Corrida de medicion del pipeline conversacional local (version A / serial).

Protocolo:
  1. Calentamiento: N_CALENTAMIENTO peticiones descartadas, para forzar la carga
     del modelo en VRAM y evitar que el cold start contamine la muestra.
  2. Corrida: REPETICIONES pasadas sobre los 10 enunciados del corpus, en orden
     aleatorizado con semilla fija, para que una deriva temporal del sistema
     (por ejemplo, throttling termico) no quede confundida con el efecto del
     enunciado.
  3. Registro: los ids devueltos por la API se guardan en corrida_ids.csv, lo que
     permite aislar en el analisis exactamente las filas de esta corrida.

Requiere que main.py devuelva la cabecera X-Id.

Uso:  docker exec orquestador_api python /app/medir.py
"""

import csv
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests  # type: ignore[reportMissingModuleSource]

API_URL = os.getenv("API_URL", "http://localhost:8000/conversar")
CORPUS_DIR = Path("/mediciones/corpus")
MANIFIESTO = CORPUS_DIR / "manifiesto.csv"
IDS_PATH = Path("/mediciones/corrida_ids.csv")

REPETICIONES = int(os.getenv("REPETICIONES", "10"))
N_CALENTAMIENTO = int(os.getenv("N_CALENTAMIENTO", "3"))
PAUSA_S = float(os.getenv("PAUSA_S", "2.0"))
SEMILLA = int(os.getenv("SEMILLA", "42"))


def cargar_manifiesto() -> list[dict]:
    if not MANIFIESTO.exists():
        print(f"ERROR: falta {MANIFIESTO}. Ejecuta antes generar_corpus.py", file=sys.stderr)
        sys.exit(1)
    with MANIFIESTO.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def enviar(id_enunciado: str) -> dict | None:
    ruta = CORPUS_DIR / f"{id_enunciado}.wav"
    t0 = time.perf_counter()
    try:
        with ruta.open("rb") as fh:
            r = requests.post(API_URL, files={"audio": (ruta.name, fh, "audio/wav")}, timeout=300)
        ms_cliente = round((time.perf_counter() - t0) * 1000, 2)
        if r.status_code != 200:
            print(f"    fallo HTTP {r.status_code}: {r.text[:160]}", file=sys.stderr)
            return None
        h = r.headers
        return {
            "id_peticion": h.get("X-Id", ""),
            "ms_total_servidor": float(h.get("X-Ms-Total", 0)),
            "ms_stt": float(h.get("X-Ms-Stt", 0)),
            "ms_llm": float(h.get("X-Ms-Llm", 0)),
            "ms_tts": float(h.get("X-Ms-Tts", 0)),
            "ms_total_cliente": ms_cliente,
        }
    except Exception as e:
        print(f"    excepcion: {e}", file=sys.stderr)
        return None


def main() -> int:
    manifiesto = cargar_manifiesto()
    banda_por_id = {m["id_enunciado"]: m["banda"] for m in manifiesto}
    ids = [m["id_enunciado"] for m in manifiesto]

    print(f"Corpus: {len(ids)} enunciados | repeticiones: {REPETICIONES} "
          f"| mediciones previstas: {len(ids) * REPETICIONES}")

    # --- Calentamiento (descartado) ---
    print(f"\nCalentamiento ({N_CALENTAMIENTO} peticiones, se descartan)")
    for i in range(N_CALENTAMIENTO):
        res = enviar(ids[0])
        marca = f"{res['ms_total_servidor']:.0f} ms" if res else "fallo"
        print(f"  calentamiento {i + 1}/{N_CALENTAMIENTO}: {marca}")
        time.sleep(PAUSA_S)

    # --- Orden aleatorizado con semilla fija ---
    plan = [(eid, rep) for rep in range(1, REPETICIONES + 1) for eid in ids]
    random.Random(SEMILLA).shuffle(plan)

    inicio = datetime.now(timezone.utc).isoformat()
    filas, fallos, consecutivos = [], 0, 0

    print(f"\nCorrida ({len(plan)} mediciones, orden aleatorizado, semilla {SEMILLA})")
    t_arranque = time.perf_counter()

    for n, (eid, rep) in enumerate(plan, start=1):
        res = enviar(eid)
        if res is None:
            fallos += 1
            consecutivos += 1
            if consecutivos >= 5:
                print("\nABORTADO: 5 fallos consecutivos. Revisa docker compose logs orquestador.",
                      file=sys.stderr)
                break
            continue
        consecutivos = 0
        res.update({
            "orden": n,
            "id_enunciado": eid,
            "banda": banda_por_id[eid],
            "repeticion": rep,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        filas.append(res)
        print(f"  [{n:3d}/{len(plan)}] {eid} r{rep}  "
              f"total {res['ms_total_servidor']:7.1f}  "
              f"stt {res['ms_stt']:6.1f}  llm {res['ms_llm']:7.1f}  tts {res['ms_tts']:7.1f}")
        time.sleep(PAUSA_S)

    campos = ["orden", "id_enunciado", "banda", "repeticion", "timestamp", "id_peticion",
              "ms_stt", "ms_llm", "ms_tts", "ms_total_servidor", "ms_total_cliente"]
    with IDS_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    dur_min = (time.perf_counter() - t_arranque) / 60
    print(f"\nCorrida finalizada en {dur_min:.1f} min")
    print(f"Mediciones validas: {len(filas)} | fallos: {fallos}")
    print(f"Inicio (UTC): {inicio}")
    print(f"Salida: {IDS_PATH}")
    print("\nSiguiente paso:  python /app/analizar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
