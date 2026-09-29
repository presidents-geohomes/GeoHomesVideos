#!/usr/bin/env python3
"""Intenta leer el saldo de la API de Higgsfield y lo anota en banco/saldo_log.json.
Uso: python3 sistema/saldo.py <etiqueta>   (p. ej. antes / despues)
No falla nunca: si no encuentra el saldo, anota qué respondió cada ruta."""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
import generar_higgsfield as hf

RUTAS = ["/v1/balance", "/balance", "/v1/account", "/account", "/v1/me", "/me",
         "/v1/credits", "/credits", "/v1/billing/balance", "/billing/balance", "/v1/users/me"]


def main():
    etiqueta = sys.argv[1] if len(sys.argv) > 1 else "saldo"
    if not hf.CLAVE:
        return
    info = {"etiqueta": etiqueta, "fecha": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rutas": {}}
    for r in RUTAS:
        try:
            d = hf.llamar(hf.BASE + r)
            texto = json.dumps(d)
            # nunca guardar claves ni correos completos
            for k in ("key", "secret", "token", "email"):
                if k in texto.lower():
                    d = {kk: vv for kk, vv in d.items() if not any(x in kk.lower() for x in ("key", "secret", "token", "email"))} if isinstance(d, dict) else "(omitido)"
            info["rutas"][r] = d
        except Exception as e:
            info["rutas"][r] = str(e)[:120]
    os.makedirs("banco", exist_ok=True)
    ruta = "banco/saldo_log.json"
    log = json.load(open(ruta)) if os.path.exists(ruta) else []
    log.append(info)
    json.dump(log[-200:], open(ruta, "w"), ensure_ascii=False, indent=1)
    print("Saldo:", {k: (v if not isinstance(v, str) else v[:40]) for k, v in info["rutas"].items()})


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("saldo: ", e)
