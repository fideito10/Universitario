# Migración de Google Sheets a PostgreSQL

Brief de ejecución para el agente. Leer completo antes de tocar código.

## 1. Objetivo

La app (Streamlit en Railway) lee y escribe directamente en Google Sheets en cada click de cada
usuario. Todos comparten una sola cuenta de servicio con tope de ~60 lecturas/minuto, así que con
pocos usuarios simultáneos se traba (429, reintentos con sleep, ~12-16 llamadas a la API por click).

**Meta:** la navegación del usuario no genera NINGUNA llamada a Google Sheets. La app lee de
PostgreSQL. Sheets queda solo como puerta de entrada de los Google Forms, sincronizada por un job.

## 2. Principios de diseño

1. **Capa de repositorio con la misma firma.** Cada loader actual devuelve un `DataFrame` (o el
   dict `{'success','data',...}` de `read_google_sheet_with_headers`). La nueva capa devuelve
   EXACTAMENTE lo mismo. Los módulos de UI (dashboard_360, áreas, panel_partido) no cambian su lógica.
2. **Datos de formularios como JSONB.** Los headers de los Forms son texto libre y el código los
   busca de forma flexible (`buscar_columna_flexible`, `buscar_columna_dni`). No normalizar columnas:
   guardar la fila cruda en `jsonb` más columnas tipadas de clave (`dni`, `fecha`, `row_hash`).
   Reconstruir el DataFrame desde el JSONB preserva los nombres de columna originales.
3. **Datos propios de la app, tablas tipadas.** Usuarios, jugadores, wellness, asistencias.
4. **Feature flag.** `DATA_BACKEND=sheets|postgres` (env var). Permite rollback inmediato sin deploy.
5. **Paridad verificable.** Cada loader migrado tiene un test que compara DataFrame de Sheets vs
   Postgres (mismas columnas, mismo orden, mismo conteo de filas, mismos valores como `str`).

## 3. Inventario actual (verificado en el código)

| Fuente (Sheet ID) | Pestaña | Quién lee | Quién escribe | Dueño del dato |
|---|---|---|---|---|
| `1Lb-ngyj...` (central) | `Usuarios` | `src/security/auth.py` | auth (alta admin por defecto) | App |
| `1Lb-ngyj...` | `Jugadores_Maestro` | administracion.py, bot.py, wellness.py, areanutricion.py (`conectar_base_central`), auth.py (login DNI), dashboard_360 | administracion.py (`add_player`, `update_player_status`) | App |
| `1Lb-ngyj...` o `1zGyW...` | `Wellness_Jugador` | wellness.py | wellness.py, google_sheets_manager.py | App |
| `1Lb-ngyj...` o `1zGyW...` | `Asistencias` | Lista.py | Lista.py | App |
| `1ham2WSM...` (médica) | 1ra hoja / `Respuestas de formulario 1` | areamedica.py, reportemedico.py, bot.py, dashboard_360 | Google Form + areamedica.py:413 | **Form** |
| `1CpAklgx...` (nutrición) | `Respuestas de formulario 1` | areanutricion.py, areafisica.py:144, dashboard_360 | Google Form + areanutricion.py:70 | **Form** |
| `1sR4wWsA...` (física) | `Base Test` | areafisica.py `cargar_hoja`, bot.py, dashboard_360 | Externo (staff) | **Externo** |
| `1JXKJkDY...` (partidos) | 1 pestaña por partido | panel_partido.py `_get_all_matches`, `_load_match_data` | Externo (análisis) | **Externo** |

Los IDs están hardcodeados en 9 archivos. Centralizarlos en `src/data/sources.py`.

"Dueño = App": la app es la fuente de verdad, se migra una vez y se deja de leer de Sheets.
"Dueño = Form/Externo": Sheets sigue siendo la entrada; Postgres es un espejo sincronizado.

## 4. Esquema propuesto

```sql
-- Datos propios de la app
usuarios(id pk, usuario unique, clave_hash, rol, nombre, dni, email, activo, created_at)
jugadores(dni pk, nombre, apellido, categoria, posicion, estado, extra jsonb, updated_at)
wellness(id pk, dni, fecha, rpe, sueno, doms, score, nombre, email, created_at)
asistencias(id pk, fecha, categoria, dni, jugador, estado, extra jsonb, created_at)

-- Espejo de fuentes externas / formularios (una tabla, discriminada por source)
sheet_rows(
  source text,        -- 'medica' | 'nutricion' | 'fisica_base_test' | 'partido:<nombre_pestaña>'
  row_num int,        -- posición en la hoja (preserva el orden)
  row_hash text,      -- sha1 de la fila, para upsert idempotente
  dni text, fecha date null,
  data jsonb,         -- {header_original: valor_string}
  synced_at timestamptz,
  primary key (source, row_num)
)
sheet_headers(source pk, headers jsonb, synced_at)  -- orden original de columnas
sync_runs(id pk, source, started_at, finished_at, rows, status, error)
```

Índices: `sheet_rows(source, dni)`, `jugadores(dni)`, `wellness(dni, fecha)`.

Para partidos: guardar las filas crudas por pestaña (`source='partido:<nombre>'`) y seguir usando
`_parse_sheet_data` sobre `list[list[str]]` reconstruido desde la DB. No reescribir el parser.

## 5. Sincronización (Sheets → Postgres)

- Worker aparte: servicio Railway con `python -m src.data.sync` en cron cada 5 min (o loop con sleep).
- Una sola llamada `spreadsheets.values.batchGet` por spreadsheet (no `get_all_values` por pestaña).
- Upsert por `(source,row_num)`; borrar filas que ya no existen. Guardar `sync_runs`.
- Backoff exponencial en 429. Si falla, la app sigue sirviendo el último dato bueno.
- Botón "Sincronizar ahora" solo para rol Administrador (llama a la misma función, con lock
  `pg_try_advisory_lock` para evitar corridas simultáneas).
- Mostrar "Datos actualizados hace X min" en el dashboard.

## 6. Escrituras

| Hoy | Después |
|---|---|
| wellness, asistencias, alta/estado de jugador, usuarios | `INSERT/UPDATE` directo a Postgres. Sin Sheets. |
| areamedica.py:413 y areanutricion.py:70 (reportes cargados desde la app) | **Decidido:** `INSERT` directo en `sheet_rows` (fuente `medica` / `nutricion`) como destino principal. El dato queda visible al instante en toda la app. El `append_row` a Sheets pasa a ser opcional y se controla con `MIRROR_WRITES_TO_SHEETS=true|false` (por defecto `false`). |
| Google Forms de médica y nutrición (se mantienen "por las dudas") | Siguen existiendo y el job de sync los trae a Postgres (hasta 5 min de demora). Para impacto inmediato el staff debe usar los formularios de la app. |

Eliminar patrones costosos: `len(get_all_values())` para contar filas, `delete_rows`, `update_cell` en loop.

## 7. Fases (cada una es un PR/commit independiente y desplegable)

**Fase 0: quick wins sin migrar (1 día, desbloquea ya)**
- `Fondo.JPG` (12,8 MB) a <300 KB; no incrustar en base64 en cada render.
- `@st.cache_data(ttl=300)` en los loaders de Sheets y reactivar el de `crear_dataframe_integrado`.
- `@st.cache_resource` para el cliente gspread y `AuthManager`/`GoogleSheetsManager`.
- Quitar `importlib.reload` de nutrición (main_universitario.py:1051) y los `time.sleep` de Lista.py.
- Aceptación: llamadas a la API por click < 2 en uso normal.

**Fase 1: infraestructura**
- Provisionar PostgreSQL en Railway, `DATABASE_URL` como variable.
- Agregar `psycopg[binary]` y `SQLAlchemy` a requirements. Engine con `@st.cache_resource` y pool chico.
- Migraciones SQL versionadas en `migrations/` (alembic o archivos numerados).
- Script `scripts/export_snapshot.py`: vuelca TODAS las pestañas a JSON local (backup + fixtures de tests).
- Aceptación: `python -m src.data.healthcheck` conecta y crea el esquema en una DB vacía.

**Fase 2: capa de datos + sync**
- `src/data/` con `sources.py`, `db.py`, `repo_*.py`, `sync.py`.
- Sync de `medica`, `nutricion`, `fisica_base_test`, partidos y `Jugadores_Maestro` (carga inicial).
- Aceptación: tests de paridad en verde para cada fuente.

**Fase 3: cambiar lecturas detrás del flag (módulo por módulo, en este orden)**
1. `dashboard_360` + `perfil_jugador` (mayor consumo)
2. `areanutricion`, `areafisica`, `areamedica`, `reportemedico`
3. `panel_partido` (quitar reintentos con sleep; `_get_all_matches` sale de DB)
4. `bot`, `kpi`
- Aceptación por módulo: con `DATA_BACKEND=postgres` la pantalla es idéntica y no hay llamadas a Sheets.

**Fase 4: datos propios de la app**
- Importar `Usuarios`, `Jugadores_Maestro`, `Wellness_Jugador`, `Asistencias` y apagar su lectura de Sheets.
- `auth.py`, `administracion.py`, `wellness.py`, `Lista.py` pasan a escribir en Postgres.
- Hash de claves (argon2/bcrypt) con migración transparente: al primer login exitoso con clave
  en texto plano, se re-hashea.

**Fase 5: cierre**
- Quitar código muerto: `google_sheets_sync.py`, `sheets_interface.py`, `scratch/`, `panel_partido1.py` si no se usa.
- Actualizar `docs/` y `CONFIGURACION_SECRETS.md`.
- Documentar el procedimiento de rollback (`DATA_BACKEND=sheets`).

## 8. Criterios de aceptación globales

1. Navegar por cualquier pantalla no dispara llamadas a `gspread` (verificable con un contador/log).
2. p95 de render de página < 1,5 s con 20 sesiones concurrentes (prueba de carga simple con `locust` o `playwright`).
3. Cero pérdida de datos: conteo de filas Sheets vs DB igual por fuente tras cada sync.
4. Los Forms siguen funcionando sin que el staff cambie nada.
5. Rollback a Sheets con una variable de entorno.

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Staff edita Jugadores_Maestro a mano en Sheets y la DB queda desactualizada | Decisión pendiente (ver 10). Hasta definirla, sincronizar también esa pestaña en modo espejo. |
| Datos desactualizados hasta 5 min | Aceptado. Botón "Sincronizar ahora" + indicador de antigüedad. |
| Cambian los headers del Form | JSONB lo tolera; los loaders siguen buscando columnas de forma flexible. |
| Fila duplicada en sync | PK `(source,row_num)` + `row_hash` idempotente. |
| Romper el login | Fase 4 al final, con fallback al flag y probando con usuarios reales de cada rol. |

## 10. Decisiones abiertas (resolver antes de la Fase 4)

Resueltas por el usuario (2026-10-12):

1. **El staff NO edita los Sheets a mano.** `Usuarios`, `Jugadores_Maestro`, `Wellness_Jugador` y `Asistencias` son propiedad de la app: se importan una sola vez y después la DB es la única fuente de verdad. No hace falta modo espejo.
2. **Se mantiene el acceso `admin/admin123`** en `auth.py`. Decisión del usuario; no tocarlo. Riesgo conocido: la clave es pública en el repo. Si más adelante se quiere endurecer, moverlo a variable de entorno sin cambiar el comportamiento.
3. **Los Forms de médica y nutrición se mantienen** por precaución, pero la carga que haga el staff desde la app debe impactar directo en la base nueva (ver sección 6).

Pendiente: retención y backups (Neon free ofrece restauración puntual limitada; confirmar en su documentación).

Base elegida: **Neon (Postgres 18, plan gratuito)**. La cadena de conexión vive en `DATABASE_URL` (`.env` local, variable de entorno en Railway). Neon suspende el cómputo por inactividad: usar `pool_pre_ping` y reintento corto en la primera conexión.

## 11. Qué NO hacer

- No reescribir la lógica de análisis ni de UI.
- No normalizar los datos de formularios a columnas fijas en esta migración.
- No borrar nada de Sheets. Siguen siendo el respaldo y la entrada de datos.
- No commitear credenciales ni `DATABASE_URL`.

## 12. Estado Fase 2 (capa de datos + sync) - completada 2026-10-12

### Inventario real (corrige la seccion 3)

| Clave (`src/data/sources.py`) | Sheet | Pestanas | Filas (get_all_values, con header) |
|---|---|---|---|
| `central` | "UnI Base de datos" `1Lb-ngyj...` | `Jugadores_Maestro` (496), `Usuarios` (4), `Wellness_Jugador` (3) | no tiene `Asistencias` |
| `medica` | "Uni Reporte Medico" `1ham2WSM...` | `Reportes` | 1 (solo header, 18 columnas genericas "Columna N") |
| `nutricion` | "Uni Nutricion" `1CpAklgx...` | `Respuestas de formulario 1` | 295 |
| `fisica` | "Uni Base Fisica " `1sR4wWsA...` | `Base Test` | 1593 (14 columnas, 3 sin nombre, 2 duplicadas) |
| `partidos` | "Datos Partidos " `1JXKJkDY...` | 23 pestanas, una por partido | 10.350 en total |
| `legacy_car` | "CAR Rugby Club - Reporte Medico (respuestas)" `1zGyW-M_...` | `Respuestas de formulario 1` | 84 |

- `1zGyW...` NO lo usa nada vivo: solo es el valor por defecto de `FormulariosGoogleSheets`
  (`src/sheets/formularios_google_sheets.py`, `worksheet_name='Hoja 1'`), y `wellness.py` y
  `GoogleSheetsManager` lo pisan con el central. No se sincroniza ni se importa.
- **Asistencias**: `Lista.py` usa `AsistenciaManager.sheet_id = 1Lb-ngyj...` (central), pestana
  `Asistencias`, que se crea on demand con `add_worksheet(rows=1000, cols=8)` y headers
  `Fecha, Categoria, Tipo_Actividad, DNI, Nombre, Apellido, Estado_Asistencia, Observaciones`.
  Hoy esa pestana no existe: nunca se guardo una asistencia. La tabla `asistencias` queda vacia.

### Comandos

```
py -m src.data.migrate                      # aplica 001 y 002 (002 relaja PK de jugadores, agrega clave_es_hash, orden, extra)
py scripts/export_snapshot.py               # backup JSON en data_snapshot/ (ignorado por git)
py -m src.data.sync [--source X] [--dry-run]  # X: medica|nutricion|fisica_base_test|partidos|partido:<nombre>
py scripts/import_app_tables.py [--dry-run] [--force]   # import unico; omite tablas ya cargadas
py -m pytest tests/test_parity.py -v        # paridad en vivo (requiere credenciales + DB)
```

### Diseno

- `src/data/sources.py`: IDs/pestanas con override `SHEET_ID_<CLAVE>` / `TAB_<CLAVE>`.
  Los modulos todavia NO lo usan (Fase 3).
- `src/data/sync.py`: 1 metadata + 1 `values.batchGet` por spreadsheet; upsert por `row_hash`
  (hash de headers+fila); borra filas desaparecidas; lock `pg_try_advisory_xact_lock`
  (pgbouncer-safe); backoff exponencial en 429/5xx; registra `sync_runs`.
  Reutilizable via `run_sync()` para el boton "Sincronizar ahora".
- `sheet_rows.data` usa claves unicas (`nombre_2` para duplicados, `__blank__N` para vacios);
  los headers originales exactos y su orden estan en `sheet_headers`. jsonb no preserva el
  orden de claves: el orden sale siempre de `sheet_headers`.
- Pestanas de partidos: `sheet_headers` `source='__partidos_index__'` guarda su orden.
- `dni` normalizado (solo digitos, sin `.0`) y `fecha` (Marca temporal/Fecha) en `sheet_rows`.
- Filas que la app inserte directo en `sheet_rows` (medica/nutricion) deben usar
  `row_num >= 1.000.000` (`rows.APP_ROW_BASE`): el sync nunca las borra y `repo` las
  devuelve al final, ordenadas por `row_num`.
- `src/data/repo.py`: `df_medica`, `df_nutricion`, `df_fisica_base_test`, `rows_partido`,
  `lista_partidos`, `df_jugadores`, `df_usuarios`, `df_wellness`. Replican el tratamiento
  de cada loader (dicts por fila, drop `Unnamed`, unicas/blank, `numericise_all`).
- App tables: la fila cruda va en `extra` y los headers en `sheet_headers` (`app:<tabla>`).
  `usuarios.clave_hash` guarda la clave en texto con `clave_es_hash=false` (re-hash en Fase 4).
  `jugadores` ya no tiene PK por DNI (el Sheet tiene DNIs duplicados y 1 vacio); PK = `id`.
  `wellness.dni` es nullable (la hoja identifica por nombre/email).

### Resultados (Sheets vs DB)

| Fuente | Filas de datos Sheets | Filas DB | Paridad |
|---|---|---|---|
| medica (`Reportes`) | 0 (solo header) | 0 (+ headers) | OK |
| nutricion | 294 | 294 (294 con dni) | OK |
| fisica_base_test | 1592 | 1592 (829 con dni, 852 con fecha) | OK |
| partidos | 10.327 en 23 pestanas | 10.327 en 23 fuentes | OK (filas crudas identicas) |
| jugadores | 495 | 495 | OK incl. tipos int/float |
| usuarios | 3 | 3 | OK |
| wellness | 2 | 2 | OK |

- Segunda corrida de sync: 0 insertadas / 0 actualizadas / 0 borradas (idempotente).
- Paridad: 16/16 tests verdes, incluyendo comparacion contra los loaders originales
  (`read_google_sheet_as_df`, `_leer_hoja`, `create_dataframe_from_sheet`).
- Diferencias legitimas encontradas: ninguna en datos. Notas: (a) la hoja medica esta vacia
  (solo header) y el original devuelve `None`; `repo.df_medica()` devuelve DataFrame vacio,
  que es lo que ya hacen los callers; (b) nutricion tiene ~1287 filas de grilla pero solo 295
  con contenido (la API recorta filas vacias finales, igual que antes).

### Pendiente para Fase 3

- Cambiar los modulos para usar `src/data/sources.py` y `repo.*` detras de `DATA_BACKEND`,
  con `st.cache_data(ttl=60..300)` sobre los `repo.*` (hoy sin cache, 1-2 queries por llamada).
- Cron/worker de `python -m src.data.sync` y boton "Sincronizar ahora" (`run_sync`) + "actualizado hace X min" (`sync_runs`).
- Escritura directa de medica/nutricion en `sheet_rows` con `row_num >= APP_ROW_BASE`.
- Fase 4: escrituras de usuarios/jugadores/wellness/asistencias a Postgres y re-hash de claves.

## 13. Estado Fase 3 (lecturas detras de `DATA_BACKEND`) - 2026-10-12

### Alcance

Solo las fuentes externas / de formulario: **medica, nutricion, fisica_base_test y partidos**.
`Usuarios`, `Jugadores_Maestro`, `Wellness_Jugador` y `Asistencias` SIGUEN leyendose y escribiendose
en Sheets (con el cache de Fase 0) hasta la Fase 4: leerlas de la DB mientras se escribe en Sheets
dejaria datos nuevos invisibles. Auth/login no se toco.

### Variables de entorno

| Variable | Valores | Default | Efecto |
|---|---|---|---|
| `DATA_BACKEND` | `sheets` \| `postgres` | `sheets` | `sheets` = comportamiento de siempre. `postgres` = las 4 fuentes de arriba salen de la DB. Se lee de env, `.env` o `st.secrets`. |
| `MIRROR_WRITES_TO_SHEETS` | `true` \| `false` | `false` | Solo con `postgres`: ademas de insertar en la DB, agrega el reporte (medica/nutricion) al Sheet. |
| `DATABASE_URL` | cadena Neon | - | Ya existente (Fase 1). |

### Como activar / desactivar / rollback

- **Activar:** DB migrada y sincronizada (`py -m src.data.migrate`, `py -m src.data.sync`), luego en
  Railway (servicio web) `DATA_BACKEND=postgres` y redeploy/restart. Agregar el servicio `worker`
  (Procfile: `python -m src.data.sync --loop --every 300`) con las mismas variables
  (`DATABASE_URL` + credenciales de Google).
- **Rollback inmediato:** `DATA_BACKEND=sheets` (o borrar la variable) y reiniciar. No hay migracion
  de datos que deshacer: los modulos vuelven a leer de Sheets. Los reportes cargados desde la app
  mientras estaba `postgres` y sin espejo viven solo en la DB (`row_num >= 1.000.000`); para no
  perderlos al volver a `sheets`, activar antes `MIRROR_WRITES_TO_SHEETS=true` o copiarlos a mano.
- **DB caida:** con `postgres` la app cae sola a Sheets (aviso `st.warning` una vez por sesion) y no
  reintenta la DB durante 60 s. No requiere accion.

### Que cambio

- `src/data/backend.py`: `use_postgres()`, `mirror_writes()`, wrappers `st.cache_data(ttl=300)` sobre
  `repo.*`, `fuente_para(sheet_id, pestana)` (mapea a la fuente de `sources.py`; lo que no esta en
  sources va a Sheets), `leer()` con fallback + circuito de 60 s, `mostrar_frescura()` y
  `boton_sincronizar()`.
- Loaders con rama Postgres (misma firma y retorno): `read_google_sheet_with_headers`
  (areamedica; de ahi salen `create_dataframe_from_sheet`, `obtener_df_medica` y reportemedico),
  `read_google_sheet_as_df` (areanutricion; de ahi `obtener_df_nutricion`), `cargar_hoja` y
  `obtener_pesos_por_dni` (areafisica; de ahi `obtener_df_fisica`), `_get_all_matches` y
  `_load_match_data` (panel_partido; sin reintentos con sleep, reusa `_parse_sheet_data`),
  `load_all_data` (bot; medica y fisica). Todos los demas pedidos de sheet/pestana no mapeados
  siguen en Sheets (p.ej. `conectar_base_central` y `Jugadores_Maestro`).
- Escrituras (`src/data/writer.py`, `insertar_fila` / `insertar_fila_posicional`): con `postgres`,
  `append_google_sheet_row` (reporte medico) y `guardar_reporte_seguro` (nutricion) insertan en
  `sheet_rows` (`row_num = max(row_num, 999.999) + 1`, `data` con los headers de `sheet_headers`, DNI
  normalizado, fecha) en una transaccion con `pg_advisory_xact_lock` (sin estado de sesion) y limpian
  el cache. Si la DB falla, la escritura cae a Sheets como hoy.
- Espejo: con `MIRROR_WRITES_TO_SHEETS=true` se hace primero el append a Sheets y luego el insert en
  la DB marcando `data.__mirrored__` (epoch). El sync borra esa copia local cuando ya leyo la fila
  desde el Sheet, para que no quede duplicada.
- Sync: `py -m src.data.sync --loop --every 300` (worker). Boton **Sincronizar ahora** en la barra
  lateral (solo rol `Administrador` y backend `postgres`; spinner + limpia cache) y texto
  "Datos actualizados hace X min" en el Home (desde `sync_runs`, la fuente mas atrasada).
- Procfile: nueva linea `worker:` (la `web:` no cambio).

### Bug de Fase 0 corregido en esta fase

`src/utils/cache.py` (`cache_si_ok`): con Streamlit 1.59 todas las funciones decoradas compartian la
misma clave de `st.cache_data` (la funcion interna es identica para todas), asi que dos loaders sin
argumentos devolvian el resultado del otro y las llamadas anidadas se bloqueaban entre si (deadlock
observado en los tests). Ahora cada funcion cacheada recibe su propio `__qualname__`.

### Tests

- `tests/test_backend.py`: paridad de cada loader (Sheets en vivo vs Postgres), fallback con
  `DATABASE_URL` invalida, `insertar_fila` y limpieza de espejo en schema temporal.
- `tests/test_smoke_app.py`: `AppTest` de las pantallas con ambos backends.

### Diferencias conocidas entre backends

- Frescura: con `postgres` los datos de los Forms llegan con hasta 5 min de demora (sync); los
  reportes cargados desde la app son inmediatos.
- Hoja medica: hoy tiene solo header (0 filas de datos). `read_google_sheet_with_headers` devuelve
  `success=True` con `data=[]` en ambos backends (misma estructura, incluida `raw_data`); `main_streamlit`
  muestra "No se pudieron cargar los datos" en ambos. Hoja totalmente vacia: `success=False` en ambos.
- `bot.py`: con `postgres` la hoja medica/fisica llega como strings (como `get_all_values`) en lugar
  de numerica (`get_all_records`); solo cambia el formato del texto que ve el modelo.
- Con `postgres` y DB sin sincronizar (sin headers) las pantallas ven datos vacios, no caen a Sheets:
  correr el sync antes de activar el flag.
