"""
Analisis de la corrida de medicion.

Cruza corrida_ids.csv (mediciones de la corrida) con latencias.csv (registro
completo de la API) para recuperar tokens generados y transcripciones, y produce:

  - Estadisticos descriptivos por etapa: n, media, DE, min, mediana, p95, max
  - Reparto porcentual de la latencia total entre etapas
  - Desagregacion por banda de longitud del enunciado
  - Relacion entre tokens generados y latencia del LLM
  - Contraste contra el umbral conversacional de referencia (200 ms)
  - Inventario de discrepancias de transcripcion para revision manual

Salida: /mediciones/resultados.md

Uso:  docker exec orquestador_api python /app/analizar.py
"""

import csv
import statistics as st
import sys
from pathlib import Path

CORRIDA = Path("/mediciones/corrida_ids.csv")
LATENCIAS = Path("/mediciones/latencias.csv")
MANIFIESTO = Path("/mediciones/corpus/manifiesto.csv")
SALIDA = Path("/mediciones/resultados.md")

# Hueco tipico entre turnos en conversacion humana (ms). Valor de referencia:
# verificar y citar la fuente en el capitulo antes de publicar.
UMBRAL_CONVERSACIONAL_MS = 200

ETAPAS = [("ms_stt", "STT"), ("ms_llm", "LLM"), ("ms_tts", "TTS"), ("ms_total_servidor", "Total")]


def percentil(datos: list[float], p: float) -> float:
    """Percentil por interpolacion lineal (metodo inclusivo)."""
    if not datos:
        return float("nan")
    orden = sorted(datos)
    if len(orden) == 1:
        return orden[0]
    k = (len(orden) - 1) * p
    piso, techo = int(k), min(int(k) + 1, len(orden) - 1)
    return orden[piso] + (orden[techo] - orden[piso]) * (k - piso)


def resumen(datos: list[float]) -> dict:
    return {
        "n": len(datos),
        "media": st.mean(datos),
        "de": st.stdev(datos) if len(datos) > 1 else 0.0,
        "min": min(datos),
        "p50": st.median(datos),
        "p95": percentil(datos, 0.95),
        "max": max(datos),
    }


def fila_md(nombre: str, r: dict) -> str:
    return (f"| {nombre} | {r['n']} | {r['media']:.1f} | {r['de']:.1f} | {r['min']:.1f} "
            f"| {r['p50']:.1f} | {r['p95']:.1f} | {r['max']:.1f} |")


def leer_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not CORRIDA.exists():
        print(f"ERROR: falta {CORRIDA}. Ejecuta antes medir.py", file=sys.stderr)
        return 1

    filas = leer_csv(CORRIDA)
    for f in filas:
        for c in ("ms_stt", "ms_llm", "ms_tts", "ms_total_servidor", "ms_total_cliente"):
            f[c] = float(f[c])

    # Cruce con el registro de la API para recuperar tokens y transcripcion.
    detalle = {}
    if LATENCIAS.exists():
        detalle = {r["id"]: r for r in leer_csv(LATENCIAS)}

    textos = {}
    if MANIFIESTO.exists():
        textos = {m["id_enunciado"]: m["texto"] for m in leer_csv(MANIFIESTO)}

    L = []
    L.append("# Resultados de la caracterizacion de latencia\n")
    L.append(f"Mediciones validas: **{len(filas)}**  ")
    L.append("Configuracion: pipeline serial (version A), inferencia local.\n")

    # --- Descriptivos por etapa ---
    L.append("## Latencia por etapa (ms)\n")
    L.append("| Etapa | n | Media | DE | Min | Mediana | p95 | Max |")
    L.append("|---|---|---|---|---|---|---|---|")
    resumenes = {}
    for col, nombre in ETAPAS:
        r = resumen([f[col] for f in filas])
        resumenes[col] = r
        L.append(fila_md(nombre, r))
    L.append("")

    # --- Reparto porcentual ---
    total_medio = resumenes["ms_total_servidor"]["media"]
    L.append("## Reparto de la latencia total\n")
    L.append("| Etapa | Media (ms) | % del total |")
    L.append("|---|---|---|")
    suma_etapas = 0.0
    for col, nombre in ETAPAS[:3]:
        m = resumenes[col]["media"]
        suma_etapas += m
        L.append(f"| {nombre} | {m:.1f} | {100 * m / total_medio:.1f}% |")
    otros = total_medio - suma_etapas
    L.append(f"| E/S y sobrecarga | {otros:.1f} | {100 * otros / total_medio:.1f}% |")
    L.append(f"| **Total** | **{total_medio:.1f}** | **100%** |")
    L.append("")

    # --- Por banda de longitud ---
    L.append("## Desagregacion por longitud del enunciado\n")
    L.append("| Banda | n | STT medio | LLM medio | TTS medio | Total medio | DE total |")
    L.append("|---|---|---|---|---|---|---|")
    for banda in ("corta", "media", "larga"):
        sub = [f for f in filas if f["banda"] == banda]
        if not sub:
            continue
        rt = resumen([f["ms_total_servidor"] for f in sub])
        L.append(f"| {banda} | {len(sub)} | "
                 f"{st.mean([f['ms_stt'] for f in sub]):.1f} | "
                 f"{st.mean([f['ms_llm'] for f in sub]):.1f} | "
                 f"{st.mean([f['ms_tts'] for f in sub]):.1f} | "
                 f"{rt['media']:.1f} | {rt['de']:.1f} |")
    L.append("")

    # --- Tokens vs latencia del LLM ---
    pares = []
    for f in filas:
        d = detalle.get(f["id_peticion"])
        if d:
            try:
                tok = int(d["n_tokens_respuesta"])
                if tok > 0:
                    pares.append((tok, f["ms_llm"]))
            except (ValueError, KeyError):
                pass
    if len(pares) > 2:
        xs = [p[0] for p in pares]
        ys = [p[1] for p in pares]
        try:
            r = st.correlation(xs, ys)
            pend = st.linear_regression(xs, ys).slope
            L.append("## Relacion entre tokens generados y latencia del LLM\n")
            L.append(f"- Pares analizados: {len(pares)}")
            L.append(f"- Tokens por respuesta: media {st.mean(xs):.1f}, DE {st.stdev(xs):.1f}")
            L.append(f"- Correlacion de Pearson: r = {r:.3f}")
            L.append(f"- Pendiente estimada: {pend:.1f} ms por token adicional")
            L.append("")
        except Exception:
            pass

    # --- Contraste con el umbral conversacional ---
    L.append("## Contraste con el umbral conversacional\n")
    factor = total_medio / UMBRAL_CONVERSACIONAL_MS
    bajo = sum(1 for f in filas if f["ms_total_servidor"] <= UMBRAL_CONVERSACIONAL_MS)
    L.append(f"- Umbral de referencia: {UMBRAL_CONVERSACIONAL_MS} ms")
    L.append(f"- Latencia media medida: {total_medio:.1f} ms")
    L.append(f"- Factor de exceso: **{factor:.1f}x**")
    L.append(f"- Mediciones dentro del umbral: {bajo} de {len(filas)} ({100 * bajo / len(filas):.1f}%)")
    L.append("")

    # --- Discrepancias de transcripcion ---
    if detalle and textos:
        L.append("## Discrepancias de transcripcion (revision manual)\n")
        L.append("Comparacion entre el enunciado sintetizado y lo transcrito por el STT. "
                 "Se listan los casos unicos por enunciado.\n")
        vistos = set()
        n_disc = 0
        for f in filas:
            d = detalle.get(f["id_peticion"])
            if not d:
                continue
            orig = textos.get(f["id_enunciado"], "")
            trans = d.get("transcripcion", "")
            clave = (f["id_enunciado"], trans.strip().lower())
            if clave in vistos:
                continue
            vistos.add(clave)
            if orig.strip().lower().rstrip(".") != trans.strip().lower().rstrip("."):
                n_disc += 1
                L.append(f"**{f['id_enunciado']}**  ")
                L.append(f"- Emitido: {orig}  ")
                L.append(f"- Transcrito: {trans}\n")
        if n_disc == 0:
            L.append("Sin discrepancias detectadas.\n")
        else:
            L.append(f"Variantes de transcripcion divergentes: {n_disc}\n")

    texto = "\n".join(L)
    SALIDA.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"\n---\nInforme escrito en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
