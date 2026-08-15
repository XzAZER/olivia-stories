# Historias Olivia — bot de publicación

Publica automáticamente las 42 historias del plan de 3 semanas en Facebook + Instagram.

**Dato clave:** ni la API de Facebook ni la de Instagram permiten *programar* historias.
Ambas publican en el instante en que las llamás. Por eso acá no hay "programación" real:
un cron de GitHub Actions dispara a las 11:00 y 19:30 (hora Argentina) y el script decide
si en ese momento le toca publicar algo.

---

## Setup — 6 pasos

### 1. Crear el repo (tiene que ser PÚBLICO)

Instagram exige que `image_url` sea una URL accesible sin autenticación. Las raw URLs de
un repo privado piden token, y el fetcher de Meta no puede autenticarse. Como las placas
se van a publicar igual, no hay nada sensible en hacerlo público.

```bash
cd bot
git init && git add . && git commit -m "Historias Olivia"
git branch -M main
git remote add origin https://github.com/XzAZER/olivia-stories.git
git push -u origin main
```

### 2. Verificar que las placas se sirven

Abrí en el navegador, en incógnito:

```
https://raw.githubusercontent.com/XzAZER/olivia-stories/main/placas/grilla.jpg
```

Si ves la imagen, listo. Si pide login, el repo quedó privado.

### 3. Infraestructura de Meta — YA ESTÁ HECHA

Queda documentado por si hay que rehacerlo o replicarlo para otra sucursal.

| Cosa | Valor |
|---|---|
| Cuenta desarrollador | Matias Moltoni (`mnmatias3@gmail.com`) |
| App | Olivia Historias Bot — ID `1738265650827335` |
| Casos de uso | Manage messaging & content on Instagram + Manage everything on your Page |
| App Review | **No requerido** |
| Portfolio | `olivia.empanadas.escobar` (`614700221198010`) |
| Usuario del sistema | Olivia Historias Bot — ID `61593635750216`, rol Employee |
| Activos asignados | Página FB (Content) · IG olivia.empanadas.escobar (Content) · App (Develop) |
| Permisos del token | `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_manage_posts`, `pages_read_engagement` |
| Vencimiento del token | 60 días desde el 15-ago-2026 → ~**14-oct-2026** |
| FB_PAGE_ID | `555689564301742` |

Para regenerar el token: Business Settings → Users → System users → Olivia Historias Bot →
Generate token. Meta lo muestra **una sola vez**.

### 4. Cargar secrets y variables en GitHub

**Settings → Secrets and variables → Actions**

Secrets:

| Nombre | Valor |
|---|---|
| `FB_PAGE_ID` | `555689564301742` |
| `META_ACCESS_TOKEN` | el token del usuario del sistema |

> `IG_USER_ID` **no hace falta**: el script lo descubre solo pidiéndole a la API la
> cuenta de Instagram vinculada a la página. Si algún día querés forzar otra cuenta,
> agregá el secret y tiene prioridad.

Variables:

| Nombre | Valor |
|---|---|
| `RAW_BASE` | `https://raw.githubusercontent.com/XzAZER/olivia-stories/main` |

---

## Probar antes de confiarle la campaña

**Dry run** (no llama a la API):

Actions → *Historias Olivia* → Run workflow → `slot` = `2026-08-16T11:00`, `dry_run` = `true`

**Test real** — publica una historia de verdad, ahora mismo:

Actions → Run workflow → `slot` = `2026-08-16T11:00`, `dry_run` = `false`

Mirá la historia en el celular. Si salió bien en las dos redes, borrala a mano y sacá
`2026-08-16T11:00` de `state.json` para que el cron la vuelva a publicar el domingo.

Local:

```bash
pip install requests
python publish.py --dry-run
python publish.py --slot 2026-08-16T11:00 --dry-run
```

---

## Cómo funciona

- `schedule.json` — las 42 historias (fecha, hora, placa)
- `publish.py` — elige el slot que corresponde a la hora actual (ventana de ±45 min para
  absorber los atrasos de GitHub Actions) y publica
- `state.json` — los slots ya publicados. Se commitea solo. Evita duplicados si el
  workflow se re-dispara
- `placas/` — las 7 imágenes, 1080x1920

Flujo por red:

- **Facebook:** `POST /{page_id}/photos` con `published=false` → `POST /{page_id}/photo_stories`
- **Instagram:** `POST /{ig_user_id}/media` con `media_type=STORIES` → `POST /{ig_user_id}/media_publish`

---

## Cosas que te pueden morder

| Riesgo | Qué hacer |
|---|---|
| El cron de GH Actions se atrasa 5-15 min bajo carga | Ya está contemplado: ventana de ±45 min |
| El token vence el ~14-oct-2026 | La campaña termina el 5-sep, así que no llega a molestar. Si lo reusás después, regeneralo |
| FB rechaza fotos ya usadas en un post publicado | El script re-sube el archivo cada vez, así que siempre hay `photo_id` nuevo |
| Límite de 25 publicaciones/24h en IG | Hacemos 2 por día. Sin riesgo |
| Si cargaste el domingo 16 a mano | Sacá sus 2 slots de `schedule.json` o agregalos a `state.json` para que no se dupliquen |
| Falla una sola red | El script publica en la otra igual y sale con error visible en Actions |

## Si querés cancelar todo

Settings → Actions → deshabilitar el workflow. O borrá el repo.
