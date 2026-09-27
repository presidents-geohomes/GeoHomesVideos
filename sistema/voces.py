#!/usr/bin/env python3
"""Narrador con ElevenLabs.

Procesa en escenas/pendientes/ los JSON con:
  "tipo": "muestras_voz"  -> busca voces y genera una muestra de cada una.
      {"tipo": "muestras_voz", "idioma": "es", "genero": "female",
       "texto": "Frase de prueba...", "carpeta": "muestras/voces_es", "cuantas": 4}
  "tipo": "narracion"     -> genera la narración de un episodio con una voz fija.
      {"tipo": "narracion", "voice_id": "...", "texto": "...",
       "carpeta": "...", "archivo": "narracion.mp3", "idioma": "es"}

Necesita el secreto ELEVENLABS_API_KEY.
"""
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.elevenlabs.io"
CLAVE = os.environ.get("ELEVENLABS_API_KEY", "").strip()
UA = "GeoHomesVideos/1.0 (+https://github.com/presidents-geohomes/GeoHomesVideos)"
MODELO = "eleven_multilingual_v2"
TIPOS = {"muestras_voz", "narracion"}


def pedir(ruta, datos=None, binario=False):
    req = urllib.request.Request(API + ruta, method="POST" if datos is not None else "GET")
    req.add_header("xi-api-key", CLAVE)
    req.add_header("User-Agent", UA)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(datos).encode()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            cuerpo = r.read()
            return cuerpo if binario else json.loads(cuerpo or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:600]}") from None


def hablar(voice_id, texto, idioma, destino):
    audio = pedir(f"/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128", {
        "text": texto,
        "model_id": MODELO,
        "language_code": idioma,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15,
                           "use_speaker_boost": True},
    }, binario=True)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as f:
        f.write(audio)


def componer_musica(prompt, ms, destino):
    """Pista instrumental original con ElevenLabs Music (uso comercial en planes de pago)."""
    audio = pedir("/v1/music?output_format=mp3_44100_128", {
        "prompt": prompt,
        "music_length_ms": max(3000, min(int(ms), 600000)),
        "force_instrumental": True,
    }, binario=True)
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    with open(destino, "wb") as f:
        f.write(audio)


def candidatas(idioma, genero, cuantas):
    """Voces de la biblioteca pública en ese idioma y género, las más usadas primero."""
    vistas, lista = set(), []
    for uso in ("narrative_story", "advertisement", "informative_educational", ""):
        q = {"language": idioma, "gender": genero, "page_size": 30, "sort": "usage_character_count_1y"}
        if uso:
            q["use_cases"] = uso
        try:
            r = pedir("/v1/shared-voices?" + urllib.parse.urlencode(q))
        except RuntimeError as e:
            print(f"  Biblioteca no disponible ({e}); uso las voces de la cuenta.")
            break
        for v in r.get("voices", []):
            if v["voice_id"] in vistas:
                continue
            vistas.add(v["voice_id"])
            lista.append({"voice_id": v["voice_id"], "nombre": v.get("name"),
                          "acento": v.get("accent"), "descripcion": (v.get("description") or "")[:160],
                          "public_owner_id": v.get("public_owner_id"), "origen": "biblioteca"})
        if len(lista) >= cuantas * 3:
            break
    # Voces que ya están en la cuenta (prediseñadas), como respaldo
    try:
        r = pedir("/v2/voices?" + urllib.parse.urlencode({"page_size": 100}))
        for v in r.get("voices", []):
            lab = v.get("labels") or {}
            if lab.get("gender", genero) == genero and v["voice_id"] not in vistas:
                lista.append({"voice_id": v["voice_id"], "nombre": v.get("name"),
                              "acento": lab.get("accent"), "descripcion": lab.get("description", ""),
                              "origen": "cuenta"})
    except RuntimeError as e:
        print(f"  No pude listar las voces de la cuenta: {e}")
    return lista


def muestras(t):
    lista = candidatas(t.get("idioma", "es"), t.get("genero", "female"), int(t.get("cuantas", 4)))
    hechas, n = [], 0
    for v in lista:
        if n >= int(t.get("cuantas", 4)):
            break
        destino = os.path.join(t["carpeta"], f"voz_{n + 1}.mp3")
        try:
            hablar(v["voice_id"], t["texto"], t.get("idioma", "es"), destino)
        except RuntimeError as e:
            print(f"  {v['nombre']}: no se pudo usar ({e})")
            continue
        n += 1
        v["muestra"] = destino
        hechas.append(v)
        print(f"  Muestra {n}: {v['nombre']} ({v.get('acento')}) -> {destino}")
    if not hechas:
        raise RuntimeError("No se pudo generar ninguna muestra de voz")
    with open(os.path.join(t["carpeta"], "voces.json"), "w", encoding="utf-8") as f:
        json.dump(hechas, f, ensure_ascii=False, indent=2)
    return hechas


def procesar(ruta):
    nombre = os.path.basename(ruta)
    t = json.load(open(ruta, encoding="utf-8"))
    print(f"Tarea de voz {nombre}")
    try:
        if t["tipo"] == "muestras_voz":
            t["resultado"] = muestras(t)
        else:
            destino = os.path.join(t["carpeta"], t.get("archivo", "narracion.mp3"))
            hablar(t["voice_id"], t["texto"], t.get("idioma", "es"), destino)
            t["resultado"] = destino
        t["estado"], carpeta, ok = "hecho", "escenas/hechas", True
    except Exception as e:
        t.update({"estado": "error", "error": str(e)})
        carpeta, ok = "escenas/errores", False
        print(f"  ERROR: {e}")
    t["fecha"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(carpeta, exist_ok=True)
    json.dump(t, open(os.path.join(carpeta, nombre), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.remove(ruta)
    return ok


def main():
    tareas = []
    for p in sorted(glob.glob("escenas/pendientes/*.json")):
        try:
            if json.load(open(p, encoding="utf-8")).get("tipo") in TIPOS:
                tareas.append(p)
        except Exception:
            pass
    if not tareas:
        print("No hay tareas de voz.")
        return
    if not CLAVE:
        sys.exit("Falta el secreto ELEVENLABS_API_KEY en GitHub.")
    for p in tareas:
        procesar(p)


if __name__ == "__main__":
    main()
