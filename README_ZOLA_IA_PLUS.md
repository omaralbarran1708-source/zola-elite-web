# ZOLA Elite IA+ Live

## Qué trae
- selector de partidos En vivo / Hoy / Mañana / Manual
- guardado de partidos y snapshots en SQLite local (`zola_live.db`)
- recalculo de predicción en vivo según marcador + minuto + estadísticas
- integración opcional con OpenAI usando `OPENAI_API_KEY`
- configuración de claves por sesión en `⚙️ Configuración`
- soporte para `ADMIN_PASSWORD`

## Variables recomendadas en Render
- `API_FOOTBALL_KEY`
- `THE_ODDS_API_KEY`
- `OPENAI_API_KEY`
- `SPORTMONKS_API_TOKEN` (opcional)
- `ADMIN_PASSWORD` (opcional)
- `OPENAI_MODEL` (opcional, por defecto `gpt-5-mini`)

## Nota
En Render free, la base SQLite local puede reiniciarse si la instancia se recrea. Si quieres persistencia estable, el siguiente paso es moverlo a Supabase o PostgreSQL.
