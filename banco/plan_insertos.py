#!/usr/bin/env python3
"""Insertos de aparatos (3 s) montados en la casa de CADA familia, con sus colores y materiales.

Cada inserto parte de una foto del set de esa familia (la superficie real: puerta, pared, isla...)
y Grok agrega el aparato en primer plano. Luego Kling anima UNA acción clara.

Uso:
  python3 banco/plan_insertos.py fotos <id> [...]        (id = f1-ins-cerradura, f2-ins-timbre...)
  python3 banco/plan_insertos.py video <id>=<foto> [...]
  python3 banco/plan_insertos.py lista
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from plan_tomas import F, NEGATIVO  # noqa: E402

REGLA = ("Close-up product detail shot inside THIS same house, matching exactly the reference photo's materials and "
         "colors ({paleta}). Shallow depth of field, warm natural light, photorealistic, vertical 9:16. The device is "
         "a clean generic modern design: NO brand, NO logo, NO readable text or numbers on it or on any screen. "
         "No people unless stated (only a hand if stated). No text, no watermarks.")

# aparato: {f1: (base, lugar), f2: (base, lugar)}, descripcion, accion
S1 = {  # superficies familia 1
    "puerta_ext": ("ext_dia", "on the arched dark-wood front door, beside the black lanterns, sand stucco around it"),
    "puerta_int": ("sala_hacia_entrada", "on the inside of the arched dark-wood front door, warm beige stucco wall"),
    "pared_sala": ("sala", "on the warm golden-beige stucco wall of the living room"),
    "pared_cocina": ("cocina", "on the warm beige wall next to the white shaker cabinets"),
    "isla": ("cocina", "on the light quartz counter of the kitchen island"),
    "encimera": ("cocina", "on the light quartz counter by the white cabinets"),
    "techo_ext": ("ext_garaje_cerca", "under the eave above the white garage door, sand stucco and terracotta roof edge"),
    "lanai": ("lanai_piscina", "on a post of the covered lanai with the pool behind"),
    "garaje": ("garaje_interior", "on the garage wall/ceiling, glossy gray floor, black pickup and red sedan nearby"),
    "lavanderia": ("lavanderia", "in the laundry room with white cabinets and terracotta floor"),
    "cuarto": ("cuarto_principal", "in the master bedroom with warm beige walls"),
    "jardin": ("ext_dia", "in the front garden with green lawn, red tropical plants and pavers"),
    "piscina": ("lanai_piscina", "in the pool"),
    "piso_cocina": ("cocina_puerta_lavanderia", "on the terracotta tile floor next to the white laundry door"),
    "corrediza": ("sala", "at the bottom of the glass sliding door that opens to the lanai"),
    "lateral": ("ext_dia", "at the side yard between the sand stucco house and a tall hedge"),
}
S2 = {  # superficies familia 2
    "puerta_ext": ("ext_porche", "on the white front door frame on the porch, white stucco and gray shutters around it"),
    "puerta_int": ("sala_hacia_entrada", "on the inside of the white front door, white shiplap wall"),
    "pared_sala": ("sala", "on the white wall of the living room"),
    "pared_cocina": ("cocina", "on the white wall next to the white shaker cabinets"),
    "isla": ("cocina", "on the white quartz top of the navy-blue kitchen island"),
    "encimera": ("cocina", "on the white quartz counter by the white cabinets"),
    "techo_ext": ("ext_dia", "under the eave above the arched white garage door, white stucco and gray roof edge"),
    "lanai": ("patio_trasero", "on a post of the screened back porch with the garden behind"),
    "garaje": ("garaje_interior", "on the garage wall/ceiling, gray floor, white SUV and a kid's bike nearby"),
    "lavanderia": ("lavanderia", "in the laundry room with white walls, navy lower cabinets and light wood floor"),
    "cuarto": ("cuarto_principal", "in the master bedroom with white shiplap walls"),
    "jardin": ("patio_trasero", "in the backyard lawn by the raised vegetable beds"),
    "piscina": None,
    "piso_cocina": ("cocina_puerta_lavanderia", "on the light oak floor next to the white laundry door"),
    "corrediza": ("patio_trasero", "at the bottom of the back porch door"),
    "lateral": ("ext_dia", "at the side yard next to the white stucco house"),
}

A = {
 "cerradura": ("puerta_ext", "a matte black smart deadbolt lock with keypad", "The bolt turns and a small green light glows."),
 "timbre": ("puerta_ext", "a slim black video doorbell with a camera lens and a light ring", "The light ring around the button glows softly blue."),
 "cam-ext": ("techo_ext", "a compact white outdoor security camera", "The camera lens rotates slightly and a small status light blinks."),
 "cam-lanai": ("lanai", "a compact white outdoor security camera", "The camera turns slowly toward the pool/garden, status light blinks."),
 "cam-mascotas": ("pared_sala", "a small round white indoor pet camera on a shelf", "The camera head pans slowly, its small light turns on."),
 "sensor-puertas": ("puerta_int", "a small white contact sensor on the door and frame", "The door opens a little, the sensor's tiny light blinks."),
 "sensor-mov": ("pared_sala", "a small white motion sensor mounted high on the wall", "Its tiny light blinks once as a shadow passes."),
 "reflector-cam": ("techo_ext", "a black floodlight camera with two LED panels", "At dusk the floodlight switches on brightly."),
 "alarma": ("puerta_int", "a slim white alarm keypad panel with a status light ring", "The status ring changes from white to green."),
 "caja-paquetes": ("puerta_ext", "a sturdy dark gray smart package box with a lid, on the doorstep", "The lid closes and a small lock light turns green."),
 "porton": ("lateral", "a black metal smart side-yard gate with a small motor", "The gate slowly swings open."),
 "garaje": ("garaje", "a smart garage door opener motor unit on the ceiling with a small status light", "The status light turns on and the drive chain starts moving."),
 "cargador": ("garaje", "a white wall-mounted EV charger with its cable plugged in", "The charger's light bar pulses softly."),
 "interruptores": ("pared_cocina", "a sleek white smart light switch panel", "A finger taps the switch and the room light behind warms up."),
 "enchufes": ("encimera", "a small white smart plug in a wall outlet with a coffee maker plugged in", "The plug's small light turns on."),
 "escenas": ("pared_sala", "the living room with recessed lights", "All the lights dim smoothly to a cozy evening level."),
 "luces-ext": ("jardin", "small black landscape path lights along the garden", "At dusk the path lights turn on one after another."),
 "luz-noche": ("cuarto", "a small warm night light near the floor by the bedroom door", "The night light fades on softly in the dark."),
 "luz-despertar": ("cuarto", "a bedside lamp", "The lamp brightens slowly like a sunrise."),
 "tiras-led": ("pared_cocina", "a warm LED strip under the white upper cabinets", "The LED strip fades on along the cabinets."),
 "ventiladores": ("cuarto", "a white ceiling fan with wood blades", "The fan starts turning slowly and speeds up."),
 "termostato": ("pared_sala", "a round smart thermostat with a glowing ring and no readable numbers", "The ring glow shifts from warm orange to cool blue."),
 "persianas": ("corrediza", "a white motorized roller shade at the top of the window", "The shade lowers smoothly halfway."),
 "sensor-agua": ("lavanderia", "a small white water leak sensor on the floor next to the washer", "A few drops touch it and its light blinks."),
 "valvula": ("lavanderia", "a smart water shutoff valve actuator on a copper pipe", "The valve lever turns a quarter turn to closed, light turns red."),
 "humedad": ("lavanderia", "a white compact dehumidifier with a status light", "It starts running, the status light turns on, air flows gently."),
 "humo-co": ("pared_cocina", "a round white smart smoke and CO detector on the ceiling", "Its ring light pulses green once."),
 "calentador": ("garaje", "a white smart water heater with a small controller module", "The controller's light turns on."),
 "purificador": ("cuarto", "a white cylindrical air purifier with a soft light ring", "It turns on, the light ring glows and the top vent moves air."),
 "altavoz": ("isla", "the light-gray fabric smart speaker with a light ring on top", "The light ring on top glows and pulses gently."),
 "piscina": ("piscina", "underwater pool lights", "The pool lights turn on and the water glows turquoise."),
 "riego": ("jardin", "pop-up lawn sprinkler heads", "The sprinklers pop up and start spraying."),
 "robot-piscina": ("piscina", "a small robotic pool cleaner on the pool floor", "The robot glides slowly along the pool floor."),
 "podadora": ("jardin", "a compact robotic lawn mower on the lawn", "The robot mower glides slowly across the grass."),
 "comedero": ("piso_cocina", "a white automatic smart pet feeder with a small water fountain beside it", "The feeder dispenses a small portion of kibble into its tray."),
 "puerta-mascota": ("corrediza", "a small white smart pet door flap", "The pet door's light turns green and the flap swings."),
 "aspiradora": ("pared_sala", "a round white robot vacuum on the floor", "The robot vacuum glides slowly across the floor."),
 "cafetera": ("encimera", "a sleek white programmable coffee maker with a glass carafe", "Coffee starts dripping into the carafe, a light turns on."),
 "electro": ("encimera", "a white French-door refrigerator door with a small indicator light", "The refrigerator door opens slightly and the inside light comes on."),
}


def superficies(fam):
    return S1 if fam == "f1" else S2


def ids():
    out = []
    for fam in ("f1", "f2"):
        for ap, (sup, _, _) in A.items():
            if superficies(fam).get(sup):
                out.append(f"{fam}-ins-{ap}")
    return out


def partes(iid):
    fam, _, ap = iid.split("-", 2)
    sup, desc, accion = A[ap]
    base, lugar = superficies(fam)[sup]
    return fam, ap, base, lugar, desc, accion


def tarea_fotos(iid):
    fam, ap, base, lugar, desc, _ = partes(iid)
    f = F[fam]
    prompt = (REGLA.format(paleta=f["paleta"]) + f" Show {desc} {lugar}. The device fills the center of the frame; "
              "the background is softly blurred but clearly this same house.")
    extra = []
    if ap == "comedero":
        extra = [f["fichas"]["floyd" if fam == "f1" else "biscuit"]]
    return [{"tipo": "imagen", "carpeta": f"banco/fotos_insertos/{fam}", "archivo": f"{iid}_{n}.jpg",
             "formato": "9:16", "jpg": True,
             "referencias": [F[fam]["set"] + base + ".png"] + extra, "prompt": prompt} for n in (1, 2)]


def tarea_video(iid, foto):
    fam, _, _, _, _, accion = partes(iid)
    return {"carpeta": f"banco/insertos/{fam}", "archivo": f"{iid}.mp4",
            "modelo": "kling-video/v3.0/std/image-to-video", "imagen_inicial": foto,
            "duracion": 3, "crf": 21, "negativo": NEGATIVO,
            "prompt": accion + " Close-up, static camera or very slow push-in, realistic, one clear action only."}


def main():
    modo, args = sys.argv[1], sys.argv[2:]
    os.makedirs("escenas/pendientes", exist_ok=True)
    if modo == "lista":
        for i in ids():
            print(i)
        print(len(ids()), "insertos")
    elif modo == "fotos":
        n = 0
        for iid in args:
            for k, t in enumerate(tarea_fotos(iid), 1):
                json.dump(t, open(f"escenas/pendientes/banco_{iid}_{k}.json", "w"), ensure_ascii=False, indent=1)
                n += 1
        print(n, "tareas de foto")
    elif modo == "video":
        for a in args:
            iid, foto = a.split("=", 1)
            json.dump(tarea_video(iid, foto), open(f"escenas/pendientes/banco_v_{iid}.json", "w"), ensure_ascii=False, indent=1)
        print(len(args), "tareas de video")


if __name__ == "__main__":
    main()
