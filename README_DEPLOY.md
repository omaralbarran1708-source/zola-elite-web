# ZOLA Elite - despliegue web

## Opción 1: Streamlit Community Cloud
1. Sube estos archivos a un repositorio en GitHub.
2. Entra a Streamlit Community Cloud.
3. Crea una nueva app.
4. Selecciona tu repositorio.
5. Main file path: `app.py`
6. En Advanced settings agrega estos secrets:
   - `API_FOOTBALL_KEY="tu_api_key"`
   - `THE_ODDS_API_KEY="tu_api_key"`
   - `SPORTMONKS_API_TOKEN="tu_token"`
7. Deploy.

## Opción 2: Render
1. Sube esta carpeta a GitHub.
2. En Render elige **New + > Blueprint** o **Web Service**.
3. Conecta el repositorio.
4. Si usas Blueprint, Render leerá `render.yaml` automáticamente.
5. Agrega las variables de entorno:
   - `API_FOOTBALL_KEY`
   - `THE_ODDS_API_KEY`
   - `SPORTMONKS_API_TOKEN`
6. Deploy.

## Ejecutar local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notas importantes
- El archivo CSV `zola_match_history.csv` se guarda localmente. En hosting gratuito puede reiniciarse o perderse.
- Si quieres historial permanente, luego conviene migrarlo a Supabase, Firebase o una base de datos.
- Para dominio propio, después del deploy conectas tu dominio desde Render o Cloudflare.
