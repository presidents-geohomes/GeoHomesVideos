# Geo Homes LLC — Estrategia de contenido para videos cortos

> Copia de seguridad de `claude/estrategia.md` del project "Geo Homes - Content Automation" (actualizada 2026-10-05 con 011 y 012). Copiar esta versión al project para que coincidan. Si el project no está disponible, la tarea diaria usa esta copia.

Leer este documento completo antes de crear cualquier video, guion o caption. Al terminar un video: guardar los guiones en guiones/ del project, subir la carpeta del video al repo y actualizar el Registro de videos (al final).

## Dónde vive cada cosa

- Este project: estrategia (este documento), guiones JSON de los videos de texto y copia del generador (sistema/generar_video.py, logo en base64).
- Repo de GitHub presidents-geohomes/GeoHomesVideos: todo lo publicado y el sistema completo.
  - AAAA-MM/AAAA-MM-DD_NNN_tema/ (ej. 2026-09/…, 2026-10/…) → NNN_ES.mp4, NNN_EN.mp4, NNN_ES_portada.jpg, NNN_EN_portada.jpg y textos.txt (título TikTok, caption, hashtags y música de cada idioma).
  - sistema/ → generadores: musica_video.py (música), portada.py (portadas), generar_higgsfield.py (videos e imágenes IA), montar_episodio.py (episodios de familias), qa_video.py, etc.
  - assets/ → logo_navy.png y logo_white.png (logo con transparencia).
  - musica/biblioteca/ → pistas instrumentales propias.
  - familias/ → paquetes de las series de familias (ver sección al final).
  - escenas/pendientes/ → al subir un JSON aquí, GitHub Actions genera el video con Higgsfield.
  - contenido/ → copia de esta estrategia (contenido/estrategia.md) y de los guiones (contenido/guiones/).

## Qué hace Geo Homes

Convierte casas existentes en casas inteligentes en Naples, FL y el suroeste de Florida (SWFL). No hace falta construcción nueva. Instala:

- Cámaras de seguridad y timbres con cámara
- Interruptores y enchufes inteligentes (smart switches / plugs)
- Cerraduras inteligentes (smart door locks)
- Abridores de garaje inteligentes
- Persianas y cortinas motorizadas
- Termostatos inteligentes
- Sensores de agua/fugas, de movimiento, de puertas y ventanas
- Iluminación inteligente y escenas ("modo película", "modo vacaciones")
- Control por voz (Alexa, Google, Siri) y todo desde una app

## Público

- Dueños de casa en Naples, Bonita Springs, Marco Island y Fort Myers.
- Residentes de temporada (snowbirds) que dejan la casa sola meses: vigilancia remota, sensores de agua y control del clima.
- Familias ocupadas, personas mayores y sus hijos, dueños de alquileres (Airbnb).
- Comunidad hispana (en español) y mercado general (en inglés).

## Idiomas y publicación

- Cada video de texto se hace en español e inglés con el mismo diseño.
- Publicar la versión en inglés como publicación principal y la versión en español en otro horario del mismo día (o en una cuenta separada si se crea). No publicar dos videos casi idénticos seguidos en la misma cuenta.
- La versión en inglés es una adaptación natural, no traducción literal (ej.: "Sin construcción nueva" → "No new build").
- Publicación programada con Metricool (blogId 7108938, zona America/New_York): Instagram Reel + TikTok + Facebook Reel, publicación automática (EN 12:00, ES 18:00).

## Música

- El generador saca el video mudo; después se le pone una pista de la biblioteca con `python3 sistema/musica_video.py video.mp4 <id_pista> salida.mp4` (recorta, fundido final y volumen para redes).
- Cada idioma usa su propia pista, elegida según el tema. Anotar la pista en textos.txt ("Música: …" / "Music: …").
- Pistas disponibles:

| Español | Inglés | Usar para |
|---|---|---|
| es_tropical_alegre | en_upbeat_pop | Consejos, beneficios, ganchos positivos |
| es_cumbia_pop | en_funk_groove | Humor ligero, mitos y verdades, curiosidades |
| es_bachata_moderna | en_acoustic_warm | Comodidad, familia, llegar a casa, rutinas de noche |
| es_bossa_latina | en_chill_lofi | Seguridad, tranquilidad, ahorro, casa en calma |
| es_reggaeton_suave | en_tech_electronic | Tecnología, control por voz, "mira lo que hace tu casa" |
| es_tormenta_latina | en_storm_cinematic | Huracanes, tormentas, alertas, casa sola |
| es_salsa_ligera | — | Promos, celebraciones, antes y después |

- Ojo (2026-10-05): en la rama main del repo solo están los MP3 de es_bossa_latina, es_tormenta_latina, en_chill_lofi y en_storm_cinematic. Las demás pistas aparecen en biblioteca.json pero su MP3 no está subido, así que musica_video.py falla con ellas.
- Opcional: al subir se puede cambiar por un audio en tendencia de TikTok/Instagram.

## Portada

Cada versión lleva portada 1080×1920 (NNN_ES_portada.jpg / NNN_EN_portada.jpg): fotograma de la escena del gancho donde el texto se lee completo (o hecha con sistema/portada.py: título corto dentro de la zona segura 4:5 que Instagram muestra en la cuadrícula).

## Tono

Divertido pero profesional. Ganchos que reconocen una molestia cotidiana, humor ligero y cierre con una llamada a la acción clara. El lobo del logo puede aparecer como emoji 🐺.

## Reglas para los guiones

- Gancho de 8 palabras como máximo; que genere curiosidad o identificación.
- Duración total de 14 a 20 segundos, con 4 o 5 escenas.
- Máximo 4 puntos por lista, de 5 palabras o menos cada uno (también en inglés).
- No inventar precios, porcentajes de ahorro, garantías, marcas asociadas, reseñas ni testimonios.
- No afirmar que algo evita robos o daños; hablar de "ver", "avisar" y "controlar".
- Mensaje recurrente: "tu casa actual, sin construcción nueva".
- Cierre normal: "Escríbenos hoy" / "Message us today".

## Estructura estándar del guion (videos de texto)

Cinco escenas en este orden:

| # | Tipo | Contenido | Duración |
|---|---|---|---|
| 1 | hook | Pregunta o frase del gancho | 2.8 s |
| 2 | text | Con kicker ("Naples, FL" o el tipo de video, ej. "Mito vs. realidad") y la promesa corta | 2.6–2.8 s |
| 3 | list | Título + 4 puntos | 5.0 s |
| 4 | text | Sin kicker: "Tu casa actual. Sin construcción nueva." / "Your current home. No new build." (u otra frase de cierre corta) | 2.6 s |
| 5 | cta | Frase + sub: "Smart Homes · Naples, FL" + botón | 3.8 s (4.0 s con teléfono) |

- Las palabras entre \*asteriscos\* salen resaltadas en celeste; resaltar 1 a 3 palabras clave por frase.
- Total habitual: 17–17.4 s.

## Formato del archivo JSON

Campos: titulo, scenes, caption, tiktok_title (y opcional idioma, audio).

```json
{
  "titulo": "…",
  "scenes": [ … ],
  "caption": "…",
  "tiktok_title": "…"
}
```

## Caption

- Pregunta del gancho + emoji.
- 1–3 frases explicando la solución (qué ve/avisa/controla el cliente).
- Mencionar "tu casa actual en Naples, sin construcción nueva".
- Cierre con 🐺🏠.
- Si el video lleva teléfono: línea aparte "📲 Envíanos un texto al (239) 204-6336" / "📲 Text us at (239) 204-6336".
- Hashtags al final (8–10): siempre #Naples #NaplesFL #SmartHome #SWFL #GeoHomes; en español añadir #CasaInteligente #Domotica; luego 2–3 del tema (ej. #VideoDoorbell #HomeSecurity, #MitoOVerdad, #HurricaneSeason, #NaplesFlorida, #SmartHomeTech).

## tiktok_title

Una línea: el gancho + un complemento corto + un emoji.

## textos.txt (en la carpeta del video del repo)

Encabezado "VIDEO NNN - Tema", línea "Pilar: … · Teléfono: Sí/No", y por cada idioma: música, título TikTok, caption y hashtags.

## Nombres de archivo

- Project: guiones/NNN_tema_corto.json (español) y guiones/NNN_tema_corto_en.json (inglés).
- Repo: carpeta AAAA-MM/AAAA-MM-DD_NNN_tema-corto/. Copia de los guiones en contenido/guiones/.
- NNN = número del video del registro, con tres dígitos.

## Sistema de video (videos de texto)

- sistema/generar_video.py genera el video vertical 1080×1920 a 30 fps: `python3 generar_video.py guion.json salida.mp4`.
- Estilo: fondo azul marino con red de nodos animada, texto Poppins que aparece palabra por palabra, acento celeste, barra de progreso arriba, logo como marca de agua (menos en el cierre) y tarjeta blanca con logo y botón en la escena cta.
- El logo está guardado en sistema/logo_base64.txt; hay que decodificarlo a logo.png junto al script antes de generar. Alternativa equivalente: pegar assets/logo_navy.png del repo sobre fondo blanco y guardarlo como logo.png (así se hicieron el 005 y del 008 al 012). Copia del generador y logo.png ya en sistema/ del repo.
- Fuente Poppins: si no está instalada y las CDN están bloqueadas, sale del paquete npm @expo-google-fonts/poppins (npm pack) → copiar Poppins_700Bold.ttf y Poppins_500Medium.ttf a /usr/share/fonts/truetype/google-fonts/ como Poppins-Bold.ttf y Poppins-Medium.ttf.
- Ojo con los asteriscos: si una palabra resaltada va antes de un signo, el signo va dentro ("*casa?*", no "*casa*?"), o se ve el asterisco.
- Después: música (musica_video.py) y portadas.

## Videos especiales con IA

Además de los videos de texto, a veces se hace un video generado con IA (Higgsfield / Kling) subiendo un JSON a escenas/pendientes/ del repo. Ejemplos: 002 "modo ausente" y 004 "desde la luna" (astronauta que le pide a su asistente "Muéstrame mi casa" y se enciende una luz en Naples). Hasta ahora solo en español. Mismas reglas de caption, sin inventar datos.

## Teléfono (solo mensajes de texto)

- Número: (239) 204-6336. El cliente prefiere que le escriban por texto, no que llamen.
- Aparece al azar en más o menos 1 de cada 3 videos, nunca en todos. Se decide al azar una vez por día y aplica igual a las dos versiones (español e inglés).
- Cuando aparece: en la escena "cta" poner "phone": "(239) 204-6336", el botón "Envíanos un texto" / "Text us today" y duración 4.0 s. En el caption, añadir "📲 Envíanos un texto al (239) 204-6336" / "📲 Text us at (239) 204-6336".
- Nunca decir "llámanos" ni "call us".
- Revisar el registro: evitar que salga muchos días seguidos (006 y 007 salieron con teléfono; 008 a 012 sin teléfono; 013 con teléfono).

## Pilares (rotar en este orden)

1. Molestia diaria → solución (luces, garaje abierto, llaves perdidas)
2. Seguridad y tranquilidad (cámaras, timbre, cerraduras, paquetes)
3. Florida y temporada (huracanes, humedad, casa vacía en verano, calor y persianas)
4. Mito o pregunta frecuente ("¿necesito casa nueva?", "¿es complicado?", "¿funciona sin wifi?")
5. Escenas y estilo de vida (modo película, modo vacaciones, despertar con persianas)

El próximo video de texto toca el pilar 2 (Seguridad y tranquilidad).

## Banco de temas

- ¿Dejaste el garaje abierto otra vez? (usado: 008)
- Tu casa no tiene que ser nueva para ser inteligente (usado: 011)
- Abre la puerta sin buscar las llaves (usado: 013)
- Mira quién toca el timbre desde cualquier lugar (usado: 009)
- Snowbirds: vigila tu casa de Naples desde el norte
- Un sensor de agua te avisa antes de que sea tarde (usado: 010)
- Persianas que bajan solas cuando pega el sol
- Llega a casa y ya está fresca
- "Modo película" con una sola frase (usado: 007)
- Paquetes en la puerta: ve quién los deja (usado: 003)
- Apaga todo al salir con un botón
- Deja entrar al técnico sin estar en casa
- Temporada de huracanes: revisa tu casa desde el celular (usado: 005)
- ¿Dejé la plancha / la luz prendida? Revísalo desde el trabajo
- Tus papás mayores, más seguros e independientes
- Airbnb: códigos de puerta para cada huésped
- Despierta con luz natural: persianas automáticas (usado: 012)
- Luces que se prenden solas al anochecer
- 5 cosas que puedes controlar con tu voz (parecido a 004)
- Mito: "las casas inteligentes son solo para millonarios" (sin dar precios)
- Antes y después: interruptor normal vs. inteligente
- Modo vacaciones: tu casa parece habitada (parecido a 002)
- Mascotas solas en casa: míralas y háblales
- Cierra la puerta desde la cama
- Un día en una casa inteligente en Naples
- 3 señales de que tu casa necesita ser inteligente
- ¿Qué pasa si se va el internet? (explicar sin prometer)
- Timbre con cámara: habla con el repartidor desde la oficina (parecido a 009)
- El garaje se cierra solo cuando te vas (parecido a 008)
- Empieza con un solo dispositivo (usado: 006)

## Registro de videos

| # | Tema | Tipo | Pilar | Teléfono | Música ES / EN | Fecha | Guion JSON en project |
|---|---|---|---|---|---|---|---|
| 001 | ¿Todavía apagas la luz a mano? | Texto ES/EN | Molestia diaria | No | — | 2026-09-26 | Sí |
| 002 | Modo ausente | Video IA, solo ES | Escenas y estilo de vida | No | — | 2026-09-26 | No aplica |
| 003 | ¿Tu paquete sigue en la puerta? | Texto ES/EN | Seguridad y tranquilidad | No | — | 2026-09-27 | Sí |
| 004 | "Muéstrame mi casa"… desde la luna | Video IA, solo ES | Escenas y estilo de vida (control por voz) | No | — | 2026-09-28 | No aplica |
| 005 | Temporada de huracanes: revisa tu casa desde el celular | Texto ES/EN | Florida y temporada | No | (ver textos.txt) | 2026-09-28 | Sí (guiones/005_huracanes.json y _en) |
| 006 | ¿Casa inteligente? Suena complicado… | Texto ES/EN | Mito o pregunta frecuente | Sí | es_cumbia_pop / en_funk_groove | 2026-09-29 | Sí |
| 007 | "Modo película" con una sola frase | Texto ES/EN | Escenas y estilo de vida | Sí | es_bachata_moderna / en_acoustic_warm | 2026-09-30 | No (captions en el repo) |
| 008 | ¿Dejaste el garaje abierto otra vez? | Texto ES/EN | Molestia diaria | No | es_tropical_alegre / en_upbeat_pop | 2026-10-01 | Sí |
| 009 | ¿Quién está tocando tu timbre? | Texto ES/EN | Seguridad y tranquilidad | No | es_bossa_latina / en_chill_lofi | Hecho 2026-10-03, se publica 2026-10-05 | Sí |
| 010 | ¿Una fuga de agua y tú fuera? (sensor de agua) | Texto ES/EN | Florida y temporada | No | es_tormenta_latina / en_storm_cinematic | Hecho 2026-10-04, se publica 2026-10-06 | Sí |
| 011 | ¿Necesitas una casa nueva para que sea inteligente? (mito) | Texto ES/EN | Mito o pregunta frecuente | No | es_bossa_latina / en_chill_lofi | Hecho 2026-10-05 (regenerado desde guion reescrito), se publica 2026-10-07 | Sí (contenido/guiones/011_casa_nueva.json y _en) |
| 012 | ¿Y si tus persianas te despertaran? (persianas automáticas) | Texto ES/EN | Escenas y estilo de vida | No | es_bossa_latina / en_chill_lofi | Hecho 2026-10-05, se publica 2026-10-08 | Sí (contenido/guiones/012_persianas_despertar.json y _en) |
| 013 | Abre la puerta sin buscar las llaves (cerradura inteligente) | Texto ES/EN | Molestia diaria | Sí | es_bachata_moderna / en_acoustic_warm | Hecho y programado 2026-10-10 (EN 12:00+, ES 18:00) | Sí (contenido/guiones/013_llaves_puerta.json y _en) |

Siguiente número: 014.

## Series de familias (episodios con historia)

- Se hacen con la skill geohomes-series-familias ("usemos la familia 1"). Todo vive en familias/ del repo; la biblia.json de cada familia manda (personajes, ropa, casa, aparatos en su lugar, reglas de guion, narradora y música).
- Familia 1 · Daniel, Mariana y Floyd — español — serie "Casa que te entiende" — familias/familia_1/.
- Familia 2 · Emma, Lily y Biscuit — inglés — serie "Home, Simplified" — familias/familia_2/.
- Episodios hechos (en episodios/hechos/): ES 001 Llegar a casa, ES 002 Alguien en la entrada, ES 003 Llega Daniel (v2); EN 001 Lily gets home (v2).
- Reglas clave: orden causa → aviso → reacción → orden → acción de la casa → resultado; una sola hora del día; la casa es la protagonista; sin marcas ni diálogos (textos en pantalla); narradora solo al final; 20–30 s. Mostrar la tabla de planos y esperar aprobación antes de generar. Marcar el contenido como IA al publicar.

## Pendientes

- Guardar en el project el guion JSON de 007 si se quiere poder regenerar (el video y los captions ya están en el repo). El de 005 ya está guardado.
- 009 y 010: resueltos el 2026-10-04 por la noche. Se regeneraron desde sus guiones, se subieron al repo (2026-10/2026-10-03_009_timbre-camara/ y 2026-10/2026-10-04_010_sensor-agua/) y se programaron en Metricool con publicación automática: 009 el lunes 2026-10-05 y 010 el martes 2026-10-06 (EN 12:00, ES 18:00).
- 011: resuelto el 2026-10-05. Como el guion original no estaba en el repo, se reescribió (contenido/guiones/011_casa_nueva*.json), se regeneró, se subió a 2026-10/2026-10-05_011_casa-nueva/ y se programó para el miércoles 2026-10-07 (EN 12:00, ES 18:00). Si el project tiene otros guiones 011, los del repo son los publicados.
- 012 (2026-10-05): subido a 2026-10/2026-10-05_012_persianas-despertar/ y programado el jueves 2026-10-08 (EN 12:00, ES 18:00). El siguiente día libre en Metricool es el viernes 2026-10-09.
- La tarea programada "Video diario Geo Homes" no podía hacer push al repo (falló el 03, el 04 y el 05). El 2026-10-05 una sesión de Claude Code sí pudo hacer push a main. Solución: añadir presidents-geohomes/GeoHomesVideos a los repositorios de esa tarea en su configuración. El repo cambió de nombre (antes geohomesvideos), así que si la tarea tenía el nombre viejo hay que volver a añadirlo.
- Subir a musica/biblioteca/ los MP3 que faltan (ver sección Música).
