# ZOLA Elite PRO

## Qué cambia
- Interfaz tipo live-score más limpia y minimalista.
- Configuración en ventana `⚙️` con claves de sesión opcionales.
- Predicción directa sin HTML visible.
- Bloques de partido, 1X2, mejor cuota, contexto, top marcadores y comparativa.
- Soporte para `ADMIN_PASSWORD` en Render para ocultar la configuración al público.

## Variables sugeridas en Render
- `API_FOOTBALL_KEY`
- `THE_ODDS_API_KEY`
- `SPORTMONKS_API_TOKEN`
- `ADMIN_PASSWORD`

## Archivos a reemplazar
- `app.py` <- usa `app_zola_pro.py`
- opcional: copia `zola_crest.png` si quieres el logo mini
