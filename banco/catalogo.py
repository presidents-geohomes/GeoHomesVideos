#!/usr/bin/env python3
"""Genera banco/catalogo.json y banco/CATALOGO.md con todas las tomas e insertos disponibles."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import plan_tomas as pt, plan_insertos as pi

RAW = "https://raw.githubusercontent.com/presidents-geohomes/GeoHomesVideos/main/"
nombres = json.load(open("banco/nombres.json", encoding="utf-8"))


def dur(v):
    try:
        return round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                           "csv=p=0", v], capture_output=True, text=True).stdout), 2)
    except Exception:
        return None


items = []
for tid, (base, refs, cambio, accion, dificil) in pt.T.items():
    fam = tid.split("-")[0]
    v = f"banco/tomas/{fam}/{tid}.mp4"
    if os.path.exists(v):
        n = nombres.get(tid, {})
        items.append({"id": tid, "familia": fam, "tipo": "toma", "titulo": n.get("t", tid), "descripcion": n.get("d", ""),
                      "grupo": n.get("cat", ""), "personajes": refs, "archivo": v, "url": RAW + v, "segundos": dur(v),
                      "usos": 0})
for iid in pi.ids():
    fam, _, ap = iid.split("-", 2)
    v = f"banco/insertos/{fam}/{iid}.mp4"
    if os.path.exists(v):
        n = nombres.get("disp:" + ap, {})
        items.append({"id": iid, "familia": fam, "tipo": "inserto", "titulo": n.get("t", ap), "descripcion": pi.A[ap][2],
                      "palabras_clave": n.get("k", []), "archivo": v, "url": RAW + v, "segundos": dur(v), "usos": 0})
cat = {"_como_usar": ("Banco de tomas reutilizables. Tomas: 5 s, sin sonido, 1080x1920. Insertos: 3 s, usar 1-1,5 s cuando "
                      "la narración nombre el aparato. Cada toma se usa máx. 2-3 veces (sumar en 'usos'). El sonido se pone "
                      "con sistema/sonido_episodio.py."), "items": items}
json.dump(cat, open("banco/catalogo.json", "w"), ensure_ascii=False, indent=1)
lin = ["# Banco de tomas Geo Homes", "", f"{sum(i['tipo']=='toma' for i in items)} tomas y "
       f"{sum(i['tipo']=='inserto' for i in items)} insertos.", ""]
for fam, nom in (("f1", "Familia 1 · Daniel, Mariana y Floyd"), ("f2", "Familia 2 · Emma, Lily y Biscuit")):
    lin += [f"## {nom}", "", "| Toma | Qué se ve | Archivo |", "|---|---|---|"]
    for i in items:
        if i["familia"] == fam:
            lin.append(f"| {i['titulo']} ({i['tipo']}) | {i['descripcion']} | `{i['archivo']}` |")
    lin.append("")
open("banco/CATALOGO.md", "w").write("\n".join(lin))
print(len(items), "elementos en el catálogo")
