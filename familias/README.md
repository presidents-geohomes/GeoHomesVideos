# Familias de las series de Geo Homes

Cada familia es un paquete fijo. Para hacer un episodio con una familia, se usan SOLO estos archivos:

- `biblia.json`: personajes, ropa, rutinas, vehículos, casa, aparatos (cada uno en su lugar), reglas de guion, narradora y música.
- `plano.png`: plano de la casa (dónde está cada habitación y aparato).
- `personajes/`: fotos aprobadas (cara y cuerpo entero).
- `set/`: fotos fijas de la casa (exterior día/atardecer/noche, garaje abierto, cocina, sala, lavandería, garaje por dentro, cuarto, lanai y piscina).
- `vehiculos/`: vehículos aprobados, sin emblemas.
- `referencias.jpg`: tablero con todo lo aprobado.

Reglas para no cambiar nada entre episodios:
1. Cada plano parte de una foto de `set/` (o de una edición de esa foto con Grok usando la foto como referencia).
2. Personajes y vehículos se añaden editando la foto del set con las fotos de `personajes/` y `vehiculos/` como referencia.
3. Las acciones de la casa (garaje, persianas, luces) se hacen con foto inicial + foto final del set.
4. Nunca se inventa una habitación, un aparato o un vehículo nuevo sin añadirlo antes a la biblia.

| Familia | Idioma | Serie | Carpeta |
|---|---|---|---|
| Familia 1 · Daniel, Mariana y Floyd | Español | Casa que te entiende | `familias/familia_1/` |
| Familia 2 · Emma, Lily y Biscuit | Inglés | Home, Simplified | `familias/familia_2/` |
