# ZOLA Elite Superbuild

## Qué incluye
- UI más cercana a apps de live-score
- buscador y vistas En vivo / Hoy / Mañana
- IA ZOLA con OpenAI
- soporte para APIs de fútbol y cuotas
- tema claro / oscuro
- persistencia local SQLite

## Archivos importantes
- `app.py` -> archivo que debe ejecutar Render
- `requirements.txt`
- `render.yaml`
- `.streamlit/secrets.toml` -> claves de entorno locales

## Despliegue
1. Reemplaza el `app.py` actual por este.
2. Sube `zola_crest.png`.
3. En Render puedes usar:
   - `API_FOOTBALL_KEY`
   - `THE_ODDS_API_KEY`
   - `SPORTMONKS_API_TOKEN`
   - `OPENAI_API_KEY`
   - `ADMIN_PASSWORD`
4. Manual Deploy -> Deploy latest commit

## Nota
Si ya compartiste claves en otros lugares, conviene rotarlas luego.
