#!/usr/bin/env python3
"""Narrador con ElevenLabs.

Procesa en escenas/pendientes/ los JSON con:
  "tipo": "muestras_voz"  -> busca voces y genera una muestra de cada una.
      {"tipo": "muestras_voz", "idioma": "es", "genero": "female",
       "texto": "Frase de prueba...", "carpeta": "muestras/voces_es", "cuantas": 4}
  "tipo": "musica"        -> genera pistas instrumentales (biblioteca de música).
      {"tipo": "musica", "carpeta": "musica/biblioteca",
       "pistas": [{"id": "es_bachata", "idioma": "es", "estilo": "...", "usar_para": "...",
                   "prompt": "...", "segundos": 22}]}
      Añade/actualiza cada pista en <carpeta>/biblioteca.json.
  "tipo": "efectos"       -> genera efectos de sonido (ambiente, clics, ladridos...).
      {"tipo": "efectos", "carpeta": "sonidos/ES03",
       "efectos": [{"id": "ladrido_1", "texto": "one friendly dog bark...", "segundos": 1.2,
                    "influencia": 0.5, "variantes": 2}]}
      Guarda <carpeta>/<id>.mp3 (o <id>_1.mp3, <id>_2.mp3... si hay variantes).
      Con "biblioteca": true se guardan en sonidos/biblioteca/ y se anotan en su catálogo
      (añade "usar_para" a cada efecto) para reutilizarlos sin volver a pagarlos.
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
TIPOS = {"muestras_voz", "narracion", "musica", "efectos"}


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


def efecto(texto, segundos, destino, influencia=0.5):
    """Efecto de sonido con ElevenLabs (text-to-sound-effects)."""
    datos = {"text": texto, "prompt_influence": float(influencia)}
    if segundos:
        datos["duration_seconds"] = max(0.5, min(float(segundos), 30.0))
    audio = pedir("/v1/sound-generation?output_format=mp3_44100_128", datos, binario=True)
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    with open(destino, "wb") as f:
        f.write(audio)


BIBLIOTECA_EFECTOS = "sonidos/biblioteca"


def efectos(t):
    """Si t["biblioteca"] es true, los efectos se guardan en sonidos/biblioteca/ y se anotan en
    biblioteca.json para reutilizarlos en otros episodios (no se vuelven a pagar)."""
    carpeta = BIBLIOTECA_EFECTOS if t.get("biblioteca") else t["carpeta"]
    cat_ruta = os.path.join(BIBLIOTECA_EFECTOS, "biblioteca.json")
    catalogo = json.load(open(cat_ruta, encoding="utf-8")) if os.path.exists(cat_ruta) else {"efectos": []}
    hechos = []
    for e in t["efectos"]:
        n = int(e.get("variantes", 1))
        for k in range(1, n + 1):
            nombre = f"{e['id']}.mp3" if n == 1 else f"{e['id']}_{k}.mp3"
            destino = os.path.join(carpeta, nombre)
            efecto(e["texto"], e.get("segundos"), destino, e.get("influencia", 0.5))
            print(f"  Efecto {nombre}")
            hechos.append(destino)
            if t.get("biblioteca"):
                catalogo["efectos"] = [x for x in catalogo["efectos"] if x["archivo"] != destino]
                catalogo["efectos"].append({"id": os.path.splitext(nombre)[0], "archivo": destino,
                                            "texto": e["texto"], "segundos": e.get("segundos"),
                                            "usar_para": e.get("usar_para", "")})
    if t.get("biblioteca"):
        os.makedirs(BIBLIOTECA_EFECTOS, exist_ok=True)
        json.dump(catalogo, open(cat_ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return hechos


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


def biblioteca_musica(t):
    carpeta = t.get("carpeta", "musica/biblioteca")
    indice_ruta = os.path.join(carpeta, "biblioteca.json")
    indice = json.load(open(indice_ruta, encoding="utf-8")) if os.path.exists(indice_ruta) else {"pistas": []}
    por_id = {p["id"]: p for p in indice["pistas"]}
    hechas, fallos = [], []
    for p in t["pistas"]:
        destino = os.path.join(carpeta, p["id"] + ".mp3")
        try:
            componer_musica(p["prompt"], int(p.get("segundos", 22)) * 1000, destino)
        except RuntimeError as e:
            print(f"  {p['id']}: ERROR {e}")
            fallos.append(f"{p['id']}: {e}")
            continue
        entrada = {k: v for k, v in p.items()}
        entrada["archivo"] = destino
        por_id[p["id"]] = entrada
        hechas.append(destino)
        print(f"  Pista {p['id']} -> {destino}")
    indice["pistas"] = sorted(por_id.values(), key=lambda x: x["id"])
    os.makedirs(carpeta, exist_ok=True)
    json.dump(indice, open(indice_ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not hechas:
        raise RuntimeError("No se generó ninguna pista: " + "; ".join(fallos))
    return {"hechas": hechas, "fallos": fallos}


def procesar(ruta):
    nombre = os.path.basename(ruta)
    t = json.load(open(ruta, encoding="utf-8"))
    print(f"Tarea de voz {nombre}")
    try:
        if t["tipo"] == "muestras_voz":
            t["resultado"] = muestras(t)
        elif t["tipo"] == "musica":
            t["resultado"] = biblioteca_musica(t)
        elif t["tipo"] == "efectos":
            t["resultado"] = efectos(t)
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
