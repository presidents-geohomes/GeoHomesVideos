#!/usr/bin/env python3
"""Plan del banco de tomas reutilizables (familias 1 y 2).

Cada toma: base (foto del set), refs (fichas de personajes/vehículos), cambio (qué agregar o
cambiar sobre la foto base con Grok; None = usar la foto del set tal cual) y accion (prompt de
movimiento para Kling, 5 s, sin sonido).

Uso:
  python3 banco/plan_tomas.py fotos  <id> [<id> ...]   -> crea tareas de imagen (2 opciones) en escenas/pendientes/
  python3 banco/plan_tomas.py video  <id>=<ruta_foto> [...] -> crea tareas de video en escenas/pendientes/
  python3 banco/plan_tomas.py lista                    -> imprime ids con/sin foto nueva
"""
import json
import os
import sys

F = {
    "f1": {
        "set": "familias/familia_1/set/",
        "fichas": {
            "daniel": "familias/familia_1/personajes/daniel_cuerpo.png",
            "mariana": "familias/familia_1/personajes/mariana_cuerpo.png",
            "mariana_trabajo": "familias/familia_1/personajes/mariana_trabajo.png",
            "floyd": "familias/familia_1/personajes/floyd_cuerpo.png",
            "pickup": "familias/familia_1/vehiculos/pickup_daniel.png",
        },
        "paleta": ("sand-colored stucco exterior, terracotta barrel-tile roof, arched dark-wood front door with two black "
                   "lanterns, white garage door, red tropical plants and palms; interior warm golden-beige stucco walls, "
                   "soft arches, white shaker cabinets, light quartz counters, diagonal terracotta tile floor, gray sofa"),
        "gente": ("Daniel: Hispanic man, 37, short dark hair, short beard, olive henley, jeans, work boots. "
                  "Mariana: Hispanic woman, 35, long wavy dark-brown hair, cream linen clothes at home or light-blue "
                  "medical scrubs from work. Floyd: red-nose pit bull, tan coat with big white chest patch."),
    },
    "f2": {
        "set": "familias/familia_2/set/",
        "fichas": {
            "emma": "familias/familia_2/personajes/emma_cuerpo.png",
            "emma_trabajo": "familias/familia_2/personajes/emma_trabajo.png",
            "lily": "familias/familia_2/personajes/lily_cuerpo.png",
            "biscuit": "familias/familia_2/personajes/biscuit_cuerpo.png",
            "suv": "familias/familia_2/vehiculos/suv_emma.png",
        },
        "paleta": ("white stucco exterior, flat gray tile roof, arched white garage door, front porch with square white "
                   "columns and a black metal bench, gray shutters, potted palms; interior white walls with shiplap "
                   "details, white shaker cabinets, navy-blue island with white quartz, brass pendant lights, light oak "
                   "wood floor, gray sofa, white painted brick fireplace"),
        "gente": ("Emma: American woman, 41, shoulder-length honey-blonde hair, light chambray shirt and jeans at home or "
                  "navy nurse scrubs for work. Lily: girl, 9, long light-brown ponytail, yellow t-shirt, denim shorts, "
                  "lilac backpack. Biscuit: fluffy long-haired orange tabby cat with green eyes. "
                  "Lily's father NEVER appears."),
    },
}

REGLAS = ("Edit this photo. Keep the camera angle, framing, architecture, furniture, fixtures, wall colors and "
          "materials exactly as they are in the first reference photo. Only make this change: {cambio} "
          "{quien}Do NOT add any other person, animal, pet feeder, appliance, device or object that is not "
          "mentioned. People appear small in the frame, at a distance, seen from behind or from the side, faces not "
          "detailed; any phone or tablet screen faces away from the camera. Photorealistic, natural light, vertical "
          "9:16. No text, no logos, no brand emblems, no watermarks.")

DESC = {
    "daniel": "Daniel (first reference person: Hispanic man, 37, short dark hair, short beard, olive henley, jeans, work boots)",
    "mariana": "Mariana (Hispanic woman, 35, long wavy dark-brown hair, cream linen outfit)",
    "mariana_trabajo": "Mariana (Hispanic woman, 35, long wavy dark-brown hair, light-blue medical scrubs)",
    "floyd": "Floyd (red-nose pit bull, tan coat, big white chest patch)",
    "pickup": "the black full-size pickup truck with no emblems",
    "emma": "Emma (American woman, 41, shoulder-length honey-blonde hair, light chambray shirt, jeans)",
    "emma_trabajo": "Emma (American woman, 41, shoulder-length honey-blonde hair, navy nurse scrubs)",
    "lily": "Lily (girl, 9, long light-brown ponytail, yellow t-shirt, denim shorts)",
    "biscuit": "Biscuit (fluffy long-haired orange tabby cat)",
    "suv": "the pearl-white compact SUV with no emblems",
}

NEGATIVO = ("text, captions, subtitles, watermark, logo, brand badge, people talking, lip movement, distorted face, "
            "extra fingers, extra limbs, morphing, flicker, objects appearing, duplicate animals")

# id: (base, [refs], cambio | None, accion, dificil)
T = {
 # ---------------- FAMILIA 1 ----------------
 "f1-ext-dia": ("ext_dia", [], None, "Static camera. Palm fronds sway gently in the breeze, soft clouds drift slowly.", 0),
 "f1-ext-amanecer": ("ext_dia", [], "Change the time to early sunrise: soft pink and orange sky, low warm light, the two black lanterns by the door still glowing.", "Static camera. Dawn light slowly brightens, palms sway gently, clouds drift.", 0),
 "f1-ext-atardecer": ("ext_atardecer", [], None, "Very slow push-in toward the house. Palms sway, clouds drift across the sunset sky.", 0),
 "f1-ext-noche": ("ext_noche", [], None, "Static camera at night. Gentle breeze in the palms, warm windows and garden lights glow steadily.", 0),
 "f1-ext-lluvia": ("ext_dia", [], "Heavy afternoon tropical downpour: overcast gray sky, wet shiny driveway pavers, visible rain streaks, small puddles.", "Heavy rain falls steadily, drops splash on the wet pavers, palms move in the wind.", 0),
 "f1-ext-tormenta": ("ext_dia", [], "Dramatic dark storm clouds approaching, strong wind bending the palms, no rain yet, moody light.", "Dark clouds race across the sky, palm fronds whip in the strong wind.", 0),
 "f1-ext-aerea": ("ext_dia", [], "High aerial drone view looking down at this same house among similar neighboring houses in a Naples, Florida neighborhood: same sand stucco walls and terracotta roof, palms, green lawns, curving street.", "Slow smooth drone descent toward the house.", 0),
 "f1-ext-calle": ("ext_atardecer", [], "Sidewalk-level view down the quiet neighborhood street at sunset with this house on the right, similar Mediterranean houses and tall palms lining the street, no people, no moving cars.", "Slow forward dolly along the sidewalk, palms sway.", 0),
 "f1-auto-daniel-sale": ("ext_dia", ["daniel", "pickup"], "Early sunrise light. Daniel seen from behind walking down the driveway toward the black pickup parked in the driveway, holding a steel thermos.", "Daniel walks away from camera toward the pickup at a relaxed pace.", 0),
 "f1-auto-daniel": ("ext_atardecer", ["pickup", "daniel"], "The black full-size pickup (no emblems) driving on a palm-lined neighborhood street at sunset, seen from the side at a distance, the driver only a silhouette.", "The pickup drives slowly from left to right; the camera pans smoothly to follow it.", 1),
 "f1-auto-mariana": ("garaje_interior", ["mariana_trabajo"], "Inside the red electric sedan (no emblems): over-the-shoulder view of Mariana in light-blue scrubs with both hands on the steering wheel, a phone on a dashboard mount with its screen facing away from camera, warm afternoon light through the windshield, palm trees outside.", "Subtle car motion: light and palm shadows slide across the dashboard, her hands rest on the wheel.", 0),
 "f1-auto-mariana-llega": ("ext_dia", ["mariana_trabajo"], "Afternoon light. Mariana in light-blue medical scrubs carrying her canvas tote, seen from behind walking up the path toward the arched dark-wood front door.", "Mariana walks toward the front door.", 0),
 "f1-auto-pickup-entrada": ("ext_atardecer", ["pickup"], "The black pickup parked in the driveway in front of the closed white garage door, taillights glowing softly.", "Static camera. Palms sway, the sunset sky slowly shifts, taillights glow.", 0),
 "f1-auto-saludo": ("ext_atardecer", ["daniel", "mariana", "pickup"], "Daniel and Mariana hugging next to the black pickup in the driveway, far from camera, at sunset.", "They share a warm hug and sway gently; static camera.", 1),
 "f1-auto-sedan-cargando": ("garaje_interior", [], None, "Static camera. The small light on the wall charger pulses softly; nothing else moves.", 0),
 "f1-ent-floyd-puerta": ("sala_hacia_entrada", ["floyd"], "Floyd sitting in front of the arched dark-wood front door, looking at it, tail up.", "Floyd wags his tail and tilts his head, waiting.", 0),
 "f1-ent-llaves": ("sala_hacia_entrada", ["mariana"], "Mariana in cream linen seen from behind near the entrance, setting her handbag on a small wooden console table against the wall.", "She sets the bag down and straightens up.", 0),
 "f1-ent-paquete": ("ext_dia", [], "Closer view of the arched dark-wood front door and lanterns; a plain unmarked cardboard box on the doormat; a delivery person in a plain uniform without logos seen from behind walking away down the path.", "The delivery person walks away; static camera.", 0),
 "f1-ent-daniel-floyd": ("sala_hacia_entrada", ["daniel", "floyd"], "The front door open with golden afternoon light; Daniel just stepped inside and crouches slightly while Floyd jumps happily toward him.", "Floyd jumps and wags excitedly, Daniel pets him.", 1),
 "f1-coc-mariana": ("cocina", ["mariana"], "Mariana in cream linen seen from behind cooking at the stainless stove on the left, steam rising from a pan, warm evening light.", "She stirs the pan, steam rises.", 0),
 "f1-coc-cafe-daniel": ("cocina", ["daniel"], "Dim blue pre-dawn light with only the under-cabinet lights on; Daniel seen from behind at the counter pouring coffee into a mug.", "He pours coffee and lifts the mug.", 0),
 "f1-coc-desayuno": ("cocina", ["daniel", "mariana"], "Morning light; Daniel and Mariana sitting on two stools at the island with coffee mugs and breakfast plates, seen from a distance slightly from behind.", "They chat and sip coffee with small natural movements.", 0),
 "f1-coc-cena": ("cocina", ["daniel", "mariana"], "Evening with warm lights; Daniel and Mariana eating dinner at the island, seen from a distance.", "They eat and chat with small natural movements.", 0),
 "f1-coc-platos": ("cocina", ["mariana"], "Late afternoon; Mariana seen from behind at the sink under the window that looks out to the pool, washing dishes.", "She rinses a plate under running water.", 0),
 "f1-coc-celular": ("cocina", ["mariana"], "Mariana sitting at the island in profile at a distance, looking down at her phone held so the screen faces away from camera, smiling.", "She scrolls and smiles softly.", 0),
 "f1-coc-brindis": ("cocina", ["daniel", "mariana"], "Evening with warm lights; Daniel and Mariana at the island clinking wine glasses, seen from a distance.", "They clink glasses and smile, small natural movements.", 0),
 "f1-coc-floyd":("cocina", ["floyd"], "Floyd sitting on the terracotta floor next to the island looking up hopefully.", "Floyd tilts his head, licks his lips, tail sweeps the floor.", 0),
 "f1-sal-sofa": ("sala", ["daniel", "mariana"], "Night; Daniel and Mariana sitting on the gray sofa seen from behind, the TV glowing.", "Flickering TV light on them, subtle movement.", 0),
 "f1-sal-pelicula": ("sala", ["daniel", "mariana"], "Night with lights dimmed; the couple seen from behind on the sofa under a blanket with a bowl of popcorn, TV glow.", "TV light flickers softly, one of them reaches into the popcorn.", 0),
 "f1-sal-siesta": ("sala", ["daniel", "floyd"], "Saturday afternoon; Daniel asleep on the gray sofa at a distance, Floyd lying on the rug beside the sofa.", "Slow breathing, Floyd's ear twitches.", 0),
 "f1-sal-lectura": ("sala", ["mariana", "floyd"], "Mariana reading a book on the sofa at a distance, Floyd's head resting on her lap.", "She turns a page and strokes Floyd.", 0),
 "f1-sal-noche": ("sala", [], "Night; the room lit only by one soft table lamp, calm and quiet, dark outside the sliding doors.", "Static camera, almost still; soft lamp glow.", 0),
 "f1-sal-tarde": ("sala", [], None, "Afternoon sunlight slowly shifts across the floor, dust motes float in the light.", 0),
 "f1-sal-floyd-cama": ("sala_hacia_entrada", ["floyd"], "Floyd asleep curled up in his round dog bed in the corner that faces the front door.", "Slow calm breathing.", 0),
 "f1-cua-dormidos": ("cuarto_principal", ["daniel", "mariana"], "Night; dark bedroom lit by moonlight through the sliding door, the couple asleep in bed seen from a distance.", "Very slow breathing, curtains barely move.", 0),
 "f1-cua-despertar": ("cuarto_principal", [], "Early morning; soft first light just starting to enter through the sliding door, the bed slightly unmade.", "Morning light slowly brightens across the bed.", 0),
 "f1-cua-estira": ("cuarto_principal", ["mariana"], "Morning light; Mariana sitting on the edge of the bed seen from behind, stretching her arms up.", "She stretches and relaxes.", 0),
 "f1-cua-botas": ("cuarto_principal", ["daniel"], "Dawn light; Daniel sitting on the edge of the bed seen from behind, putting on his work boots.", "He laces a boot.", 0),
 "f1-cua-lee": ("cuarto_principal", ["mariana"], "Night; bedside lamp on, Mariana reading in bed at a distance.", "She turns a page.", 0),
 "f1-cua-floyd-cama": ("cuarto_principal", ["floyd"], "Floyd lying on the rug at the foot of the bed.", "Floyd rests, slow breathing, ear twitches.", 0),
 "f1-cua-hecha": ("cuarto_principal", [], None, "Soft light; the curtains move gently in a breeze.", 0),
 "f1-cua-closet": ("cuarto_principal", ["mariana"], "Mariana seen from behind in front of an open white closet, choosing a blouse.", "She slides hangers and picks a blouse.", 0),
 "f1-lav-ropa": ("lavanderia", ["mariana"], "Mariana seen from behind folding white towels on the laundry counter.", "She folds a towel.", 0),
 "f1-lav-daniel": ("lavanderia", ["daniel"], "Daniel entering through the door from the garage, seen from the side at a distance.", "He walks across the laundry room.", 0),
 "f1-gar-interior": ("garaje_interior", [], "The garage door fully open with warm afternoon sun pouring in onto the glossy floor.", "Static camera; sunlight and dust in the air, faint breeze.", 0),
 "f1-gar-herramientas": ("garaje_interior", ["daniel"], "Daniel seen from behind organizing garden tools on the wall shelves.", "He hangs a tool on the shelf.", 0),
 "f1-pas-noche": ("sala_hacia_entrada", [], "Night; the entrance hallway lit only by a dim warm night light, quiet.", "Static camera, still and calm.", 0),
 "f1-lav-floyd": ("lavanderia", ["floyd"], "Floyd trotting across the laundry room floor.", "Floyd trots across the room.", 0),
 "f1-lan-piscina": ("lanai_piscina", [], "Bright midday with blue sky, the pool water sparkling.", "Water ripples sparkle; palms sway.", 0),
 "f1-lan-luces": ("lanai_piscina", [], None, "Pool water shimmers under the lights; palms sway.", 0),
 "f1-lan-parrilla": ("lanai_piscina", ["daniel"], "Daniel seen from behind at the built-in grill on the lanai, smoke rising, sunset light.", "He flips food on the grill, smoke drifts.", 0),
 "f1-lan-tumbonas": ("lanai_piscina", ["daniel", "mariana"], "Sunset; Daniel and Mariana relaxing on lounge chairs by the pool, far from camera.", "Subtle movement, water shimmers.", 0),
 "f1-lan-nada": ("lanai_piscina", ["mariana"], "Sunny afternoon; Mariana swimming slowly in the pool, far from camera.", "She swims a slow breaststroke across the pool.", 1),
 "f1-lan-mesa": ("lanai_piscina", ["daniel", "mariana"], "Night; the couple at the lanai dining table with candles, far from camera.", "Candles flicker, they raise their glasses.", 0),
 "f1-lan-domingo": ("lanai_piscina", ["daniel", "mariana"], "Sunday morning light; breakfast on the lanai table, the couple far from camera.", "They eat and chat, pool water sparkles.", 0),
 "f1-lan-lluvia": ("lanai_piscina", [], "Heavy rain falling on the pool, seen from inside the screened lanai, gray sky.", "Rain splashes on the pool surface.", 0),
 "f1-lan-floyd": ("lanai_piscina", ["floyd"], "Daytime; Floyd lying on the pool deck in the sun.", "Floyd rests, ears twitch, water shimmers.", 0),
 "f1-lan-sirve": ("lanai_piscina", ["daniel"], "Sunset; Daniel carrying a plate from the grill to the lanai table.", "He walks and sets the plate down.", 0),
 "f1-floyd-duerme": ("sala_hacia_entrada", ["floyd"], "Closer view: Floyd asleep in his round dog bed.", "Slow calm breathing.", 0),
 "f1-floyd-levanta": ("sala_hacia_entrada", ["floyd"], "Floyd lying in his round dog bed, head raised and ears alert, looking at the front door.", "He lifts his head and perks his ears.", 0),
 "f1-floyd-corre": ("sala", ["floyd"], "Floyd running happily across the living room.", "Floyd runs across the room.", 0),
 "f1-floyd-come": ("cocina_puerta_lavanderia", ["floyd"], "Replace the two metal bowls on the mat with one white automatic smart pet feeder and a small white water fountain, and show Floyd eating from the smart feeder. No people.", "Floyd eats from the smart feeder.", 0),
 "f1-floyd-lanai": ("sala", ["floyd"], "Floyd sitting in front of the glass sliding doors looking out at the pool.", "Floyd watches, ears move, tail sweeps.", 0),
 "f1-floyd-ventana": ("sala", ["floyd"], "Floyd standing with his nose close to the glass sliding door, waiting.", "Floyd looks out and wags slowly.", 0),
 "f1-esp-vacaciones": ("ext_dia", ["daniel", "mariana"], "The couple seen from behind rolling suitcases up the path to the front door.", "They walk toward the door pulling the suitcases.", 0),
 "f1-esp-tormenta": ("sala", ["mariana"], "Dark stormy afternoon outside the sliding doors with heavy rain; Mariana seen from behind watching the storm.", "Rain streams down outside, she stands still watching.", 0),
 "f1-esp-navidad": ("ext_noche", [], "Christmas lights wrapped on the palm trunks and around the arched entrance, a wreath on the door.", "Static camera; the lights twinkle softly.", 0),
 "f1-esp-macetas": ("lanai_piscina", ["mariana"], "Daytime; Mariana seen from behind watering potted plants on the lanai.", "She waters a plant.", 0),
 # ---------------- FAMILIA 2 ----------------
 "f2-ext-dia": ("ext_dia", [], None, "Static camera. Palms sway gently, clouds drift slowly.", 0),
 "f2-ext-manana": ("ext_manana", [], None, "Static camera. Morning light slowly grows, palms sway.", 0),
 "f2-ext-atardecer": ("ext_atardecer", [], None, "Very slow push-in toward the house, sunset clouds drift.", 0),
 "f2-ext-noche": ("ext_noche", [], None, "Static camera at night; porch light and windows glow, palms sway gently.", 0),
 "f2-ext-lluvia": ("ext_dia", [], "Heavy afternoon tropical rain: overcast gray sky, wet shiny driveway and porch, rain streaks, puddles.", "Heavy rain falls steadily, palms move in the wind.", 0),
 "f2-ext-tormenta": ("ext_dia", [], "Dramatic dark storm clouds approaching, strong wind bending the palms, no rain yet.", "Dark clouds race across the sky, palms whip in the wind.", 0),
 "f2-ext-aerea": ("ext_dia", [], "High aerial drone view looking down at this same white house with gray roof among similar neighboring houses in a Naples, Florida neighborhood, palms and green lawns.", "Slow smooth drone descent toward the house.", 0),
 "f2-ext-calle": ("ext_atardecer", [], "Sidewalk-level view down the quiet neighborhood street at sunset with this white house on the left, palms lining the street, no people, no moving cars.", "Slow forward dolly along the sidewalk.", 0),
 "f2-ext-porche": ("ext_porche", [], None, "Static camera. Late light, potted palms sway gently.", 0),
 "f2-auto-emma-sale": ("ext_manana", ["emma_trabajo", "suv"], "Before sunrise, porch light on; Emma in navy scrubs with a coffee cup seen from behind walking toward the white SUV in the driveway.", "Emma walks toward the SUV.", 0),
 "f2-auto-emma": ("ext_manana", ["suv", "emma_trabajo"], "The pearl-white compact SUV (no emblems) driving on a palm-lined street at sunrise, seen from the side at a distance, driver only a silhouette.", "The SUV drives slowly from left to right; the camera pans smoothly.", 1),
 "f2-auto-emma-celular": ("garaje_interior", ["emma_trabajo"], "Night: inside the white SUV parked, Emma in navy scrubs seen over the shoulder looking at her phone with the screen facing away from camera, soft dashboard glow.", "She scrolls slowly, soft light on her face from the side.", 0),
 "f2-auto-emma-llega": ("ext_noche", ["emma_trabajo", "suv"], "Night; the white SUV parked in the driveway, Emma in navy scrubs seen from behind walking from the SUV to the lit porch.", "Emma walks toward the porch.", 0),
 "f2-auto-suv-entrada": ("ext_noche", ["suv"], "The pearl-white SUV parked in the driveway at night, headlights and interior lights on.", "Static camera; lights glow, palms sway.", 0),
 "f2-auto-lily-llega": ("ext_porche", ["lily"], "Afternoon; Lily with her lilac backpack seen from behind walking from the sidewalk up to the porch.", "Lily walks up the path to the porch.", 0),
 "f2-auto-abrazo": ("ext_porche", ["emma", "lily"], "Emma and Lily hugging on the front porch, far from camera, late afternoon.", "They hug and sway gently.", 1),
 "f2-auto-compras": ("ext_porche", ["emma"], "Emma seen from behind carrying grocery bags up the path to the porch.", "Emma walks to the porch with the bags.", 0),
 "f2-ent-biscuit": ("sala_hacia_entrada", ["biscuit"], "Biscuit sitting in front of the white front door, looking at it.", "Biscuit's tail curls, ears turn toward the door.", 0),
 "f2-ent-mochila": ("sala_hacia_entrada", ["lily"], "Lily seen from behind hanging her lilac backpack on the hook by the door.", "She hangs the backpack.", 0),
 "f2-ent-llaves": ("sala_hacia_entrada", ["emma"], "Emma seen from behind dropping her keys into a bowl on the console by the door.", "She drops the keys and walks off.", 0),
 "f2-ent-paquete": ("ext_porche", [], "A plain unmarked cardboard box on the porch by the front door; a delivery person in a plain uniform without logos seen from behind walking away.", "The delivery person walks away.", 0),
 "f2-ent-lily-biscuit": ("sala_hacia_entrada", ["lily", "biscuit"], "The front door open with afternoon light; Lily just stepped inside while Biscuit rubs against her legs, seen from down the hall.", "Biscuit rubs against her legs, she bends to pet him.", 1),
 "f2-coc-juntas": ("cocina", ["emma", "lily"], "Emma and Lily cooking together at the navy island, seen from a distance, warm light.", "They stir and chop with small natural movements.", 0),
 "f2-coc-tareas": ("cocina", ["lily"], "Lily doing homework at the navy island, in profile at a distance, notebook open.", "She writes and taps her pencil.", 0),
 "f2-coc-cafe": ("cocina", ["emma_trabajo"], "Early morning; Emma in navy scrubs seen from behind at the counter holding her coffee cup.", "She sips coffee and looks out the window.", 0),
 "f2-coc-desayuno": ("cocina", ["emma", "lily"], "Morning; Emma and Lily having breakfast at the island, seen from a distance.", "They eat and chat.", 0),
 "f2-coc-cena": ("cocina", ["emma", "lily"], "Evening with pendant lights on; Emma and Lily eating dinner at the island, from a distance.", "They eat and chat.", 0),
 "f2-coc-celular": ("cocina", ["emma"], "Emma at the island in profile at a distance, looking at her phone with the screen facing away, smiling.", "She scrolls and smiles.", 0),
 "f2-coc-noche": ("cocina", [], "Night; only the under-cabinet lights and one pendant dimmed, calm kitchen.", "Static camera, still.", 0),
 "f2-coc-vacia": ("cocina", [], None, "Morning light slowly moves across the island and floor.", 0),
 "f2-sal-pelicula": ("sala", ["emma", "lily"], "Night with lights low; Emma and Lily seen from behind on the gray sofa under a blanket with popcorn, TV glow over the fireplace.", "TV light flickers softly.", 0),
 "f2-sal-lectura": ("sala", ["lily", "biscuit"], "Lily reading a book on the sofa with Biscuit curled on her lap, at a distance.", "She turns a page and strokes Biscuit.", 0),
 "f2-sal-emma-duerme": ("sala", ["emma_trabajo"], "Morning; Emma asleep on the sofa under a blanket, still in navy scrubs, at a distance.", "Slow breathing.", 0),
 "f2-sal-noche": ("sala", [], "Night; the living room lit by one soft lamp, the white fireplace calm.", "Static camera, still.", 0),
 "f2-sal-tarde": ("sala", [], None, "Golden afternoon light slowly shifts across the sofa and floor.", 0),
 "f2-sal-ventana": ("sala", ["biscuit"], "Biscuit curled up asleep on the window seat in the sun.", "Slow breathing, tail tip moves.", 0),
 "f2-sal-videollamada": ("sala", ["lily"], "Lily on the sofa holding a tablet up for a video call, the tablet screen faces away from camera, smiling, at a distance.", "She waves at the tablet and laughs silently.", 0),
 "f2-cua-lily-duerme": ("cuarto_lily", ["lily", "biscuit"], "Night; the room lit only by the warm string lights, Lily asleep in her bed seen from a distance, Biscuit curled at her feet.", "Slow calm breathing, string lights glow.", 0),
 "f2-cua-despertar": ("cuarto_lily", ["lily"], "Early morning soft light; Lily sitting up in bed seen from behind, stretching.", "She stretches her arms.", 0),
 "f2-cua-emma-dia": ("cuarto_principal", ["emma"], "Daytime with blackout curtains closed, dim room; Emma asleep in bed at a distance.", "Slow breathing, a thin line of light on the wall.", 0),
 "f2-cua-emma-lee": ("cuarto_principal", ["emma"], "Night; bedside lamp on, Emma reading in bed at a distance.", "She turns a page.", 0),
 "f2-cua-cuento": ("cuarto_lily", ["emma", "lily"], "Night with string lights on; Emma sitting on the edge of Lily's bed reading a picture book to Lily who is tucked in, seen from a distance.", "Emma turns a page, Lily snuggles.", 0),
 "f2-cua-hecha": ("cuarto_principal", [], None, "Soft light; curtains move slightly.", 0),
 "f2-cua-closet": ("cuarto_principal", ["emma_trabajo"], "Emma seen from behind in front of an open white closet holding her navy scrubs.", "She takes the scrubs off the hanger.", 0),
 "f2-lav-ropa": ("lavanderia", ["emma"], "Emma seen from behind folding towels on the laundry counter.", "She folds a towel.", 0),
 "f2-pas-noche": ("pasillo", [], "Night; the hallway lit only by a dim warm night light.", "Static camera, still.", 0),
 "f2-gar-interior": ("garaje_interior", [], None, "Static camera; soft light, dust in the air.", 0),
 "f2-lav-biscuit": ("lavanderia", ["biscuit"], "Biscuit walking calmly across the laundry room floor.", "Biscuit walks across the room.", 0),
 "f2-lav-emma": ("lavanderia", ["emma_trabajo"], "Emma in navy scrubs with her work bag entering from the garage door, seen from the side at a distance.", "She walks through the laundry room.", 0),
 "f2-pat-huerto": ("patio_trasero", ["emma"], "Emma seen from behind watering the raised vegetable garden beds with a watering can.", "Water pours onto the plants.", 0),
 "f2-pat-porche": ("patio_trasero", [], None, "Static camera; golden light, the swing moves slightly in the breeze.", 0),
 "f2-pat-cena": ("patio_trasero", ["emma", "lily"], "Evening; string lights on in the screened back porch, Emma and Lily eating at the porch table, far from camera.", "Lights glow, they eat and chat.", 0),
 "f2-pat-domingo": ("patio_trasero", ["emma", "lily"], "Sunday morning; breakfast on the back porch table, Emma and Lily far from camera.", "They eat and chat.", 0),
 "f2-pat-lluvia": ("patio_trasero", [], "Heavy rain falling on the backyard lawn and garden, seen from inside the screened back porch.", "Rain falls steadily, drops bounce.", 0),
 "f2-pat-biscuit-sale": ("patio_trasero", ["biscuit"], "Close view of the back porch door with a small white smart pet door at the bottom; Biscuit stepping out through the pet door onto the porch.", "Biscuit steps through the pet door, the flap swings closed.", 1),
 "f2-pat-noche": ("patio_trasero", [], "Night; warm string lights glowing over the back porch and the garden in silence.", "Static camera; lights glow softly.", 0),
 "f2-bis-sofa": ("sala", ["biscuit"], "Close view: Biscuit asleep curled up on the gray sofa.", "Slow breathing.", 0),
 "f2-bis-sol": ("sala", ["biscuit"], "Biscuit stretching on the wood floor in a patch of sunlight by the window.", "He stretches and relaxes.", 0),
 "f2-bis-ventana": ("sala", ["biscuit"], "Biscuit sitting on the window seat watching birds outside.", "His tail twitches as he watches.", 0),
 "f2-bis-come": ("cocina_puerta_lavanderia", ["biscuit"], "Biscuit sitting calmly and upright on the floor right next to the white automatic smart feeder (water fountain beside it), body facing the camera, head up, eyes open, relaxed, NOT eating, mouth closed, not touching the food tray.", "Biscuit sits calmly beside the feeder, slowly blinks, his tail curls gently and his ears twitch. He does not eat and does not move his mouth. Static camera.", 0),
 "f2-bis-entra": ("patio_trasero", ["biscuit"], "View from inside the back porch toward the door with a small white smart pet door; Biscuit coming in through the pet door.", "Biscuit steps in through the pet door.", 1),
 "f2-bis-pasillo": ("pasillo", ["biscuit"], "Biscuit walking calmly down the hallway toward camera.", "Biscuit walks toward camera.", 0),
 "f2-esp-vacaciones": ("ext_porche", ["emma", "lily"], "Emma and Lily seen from behind rolling suitcases up to the porch.", "They walk to the door with the suitcases.", 0),
 "f2-esp-tormenta": ("sala", ["emma", "lily"], "Dark stormy afternoon outside the windows with heavy rain; Emma and Lily seen from behind watching the storm.", "Rain streams outside, they stand still.", 0),
 "f2-esp-navidad": ("ext_noche", [], "Christmas lights on the porch columns and palms, a wreath on the front door.", "Static camera; lights twinkle softly.", 0),
 "f2-esp-cumple": ("cocina", ["emma", "lily"], "A birthday cake with lit candles on the navy island, Emma and Lily behind it seen from a distance.", "Candle flames flicker, they smile.", 0),
}


def fam(tid):
    return tid.split("-")[0]


def foto_base(tid):
    b = T[tid][0]
    return F[fam(tid)]["set"] + b + ".png"


def tarea_fotos(tid, opciones=2):
    base, refs, cambio, _, _ = T[tid]
    if cambio is None:
        return []
    f = F[fam(tid)]
    quien = ""
    if refs:
        quien = ("The only people/animals/vehicles allowed in the image are: " +
                 "; ".join(DESC[r] for r in refs) + ", matching the extra reference images. ")
    else:
        quien = "There must be NO people and NO animals in the image. "
    prompt = REGLAS.format(cambio=cambio, quien=quien)
    out = []
    for n in range(1, opciones + 1):
        out.append({"tipo": "imagen", "carpeta": f"banco/fotos/{fam(tid)}", "archivo": f"{tid}_{n}.jpg",
                    "formato": "9:16", "jpg": True,
                    "referencias": [foto_base(tid)] + [f["fichas"][r] for r in refs],
                    "prompt": prompt})
    return out


def tarea_video(tid, foto):
    _, _, _, accion, _ = T[tid]
    return {"carpeta": f"banco/tomas/{fam(tid)}", "archivo": f"{tid}.mp4",
            "modelo": "kling-video/v3.0/std/image-to-video", "imagen_inicial": foto,
            "duracion": 5, "crf": 21, "negativo": NEGATIVO,
            "prompt": accion + " Cinematic, warm natural light, smooth slow movement, realistic, no one speaks."}


def main():
    modo, args = sys.argv[1], sys.argv[2:]
    os.makedirs("escenas/pendientes", exist_ok=True)
    if modo == "lista":
        for tid in T:
            print(tid, "foto nueva" if T[tid][2] else "set", "DIFICIL" if T[tid][4] else "")
    elif modo == "fotos":
        n = 0
        for tid in args:
            for k, t in enumerate(tarea_fotos(tid, int(os.environ.get("OPCIONES", "2"))), 1):
                t["archivo"] = t["archivo"].replace(".jpg", os.environ.get("SUFIJO", "") + ".jpg")
                json.dump(t, open(f"escenas/pendientes/banco_{tid}{os.environ.get('SUFIJO', '')}_{k}.json", "w"), ensure_ascii=False, indent=1)
                n += 1
        print(n, "tareas de foto")
    elif modo == "video":
        for a in args:
            tid, foto = a.split("=", 1)
            json.dump(tarea_video(tid, foto), open(f"escenas/pendientes/banco_v_{tid}.json", "w"), ensure_ascii=False, indent=1)
        print(len(args), "tareas de video")


if __name__ == "__main__":
    main()
