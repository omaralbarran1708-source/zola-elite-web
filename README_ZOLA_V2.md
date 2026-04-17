# ZOLA Elite V2

## Cambios
- Se quitó el campo de partido manual.
- Se añadió buscador de partido.
- Se añadió selector por En vivo / Hoy / Mañana.
- Lista de competiciones y partidos inspirada en apps de live-score.
- Recalculo live con marcador actual y minuto.
- IA con `OPENAI_API_KEY` para resumen dinámico.
- Guardado de partidos seleccionados en SQLite local.
- Mejor cuota con fallback a cuota modelo si el mercado no llega.

## Variables recomendadas en Render
- API_FOOTBALL_KEY
- THE_ODDS_API_KEY
- OPENAI_API_KEY
- SPORTMONKS_API_TOKEN (opcional)

## Despliegue
Renombra `app_zola_v2.py` a `app.py` o reemplaza tu `app.py` por este archivo.
