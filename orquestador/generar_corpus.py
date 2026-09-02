"""
Generación del corpus de estímulos para la caracterización de latencia.

Sintetiza 10 enunciados de prueba con Piper y los guarda como wav en
/mediciones/corpus/. Los enunciados se agrupan en tres bandas de longitud
(corta, media, larga) para permitir el análisis del efecto de la longitud
de entrada sobre la latencia de cada etapa del pipeline.

Uso:  docker exec orquestador_api python /app/generar_corpus.py
"""

import csv
import os
import subprocess
import sys
import wave
import contextlib
from pathlib import Path

PIPER_VOICE = os.getenv("PIPER_VOICE", "/voices/es_ES-davefx-medium.onnx")
CORPUS_DIR = Path("/mediciones/corpus")
MANIFIESTO = CORPUS_DIR / "manifiesto.csv"

# Enunciados dirigidos a un agente conversacional situado en un entorno virtual.
# id, banda de longitud, texto
ENUNCIADOS = [
    ("E01", "corta", "Hola, quien eres"),
    ("E02", "corta", "Que hay en este lugar"),
    ("E03", "corta", "Puedes ayudarme"),
    ("E04", "media", "Estoy buscando la salida de este edificio, sabes por donde queda"),
    ("E05", "media", "Me puedes explicar para que sirve la maquina que esta detras de ti"),
    ("E06", "media", "Cuanto tiempo llevas trabajando aqui y que es lo que haces exactamente"),
    ("E07", "media", "No entiendo muy bien las instrucciones, me las puedes repetir mas despacio"),
    ("E08", "larga", "Antes de continuar necesito que me expliques cuales son los riesgos de "
                     "esta zona y que equipo de proteccion debo usar para poder entrar sin problemas"),
    ("E09", "larga", "Me gustaria saber si existe alguna forma de llegar hasta la parte superior "
                     "de la estructura sin tener que pasar por el sector que esta cerrado por mantenimiento"),
    ("E10", "larga", "Estuve revisando los planos que me entregaste al comienzo y creo que hay una "
                     "diferencia con lo que veo aqui, podrias confirmarme cual de las dos versiones es la correcta"),
]


def duracion_wav(path: Path) -> float:
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as f:
            return round(f.getnframes() / float(f.getframerate()), 3)
    except Exception:
        return -1.0


def main() -> int:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    if not Path(PIPER_VOICE).exists():
        print(f"ERROR: no se encuentra la voz en {PIPER_VOICE}", file=sys.stderr)
        return 1

    filas = []
    for eid, banda, texto in ENUNCIADOS:
        salida = CORPUS_DIR / f"{eid}.wav"
        proc = subprocess.run(
            ["piper", "--model", PIPER_VOICE, "--output_file", str(salida)],
            input=texto.encode("utf-8"),
            capture_output=True,
        )
        if proc.returncode != 0:
            print(f"ERROR en {eid}: {proc.stderr.decode('utf-8', 'ignore')[:300]}", file=sys.stderr)
            return 1

        dur = duracion_wav(salida)
        filas.append({
            "id_enunciado": eid,
            "banda": banda,
            "n_palabras": len(texto.split()),
            "n_caracteres": len(texto),
            "dur_audio_s": dur,
            "texto": texto,
        })
        print(f"{eid}  [{banda:5s}]  {dur:5.2f} s  {len(texto.split()):2d} palabras")

    with MANIFIESTO.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    total = sum(r["dur_audio_s"] for r in filas)
    print(f"\n{len(filas)} enunciados generados en {CORPUS_DIR}")
    print(f"Duracion total de audio: {total:.2f} s")
    print(f"Manifiesto: {MANIFIESTO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
