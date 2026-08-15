# Dónde quedamos — 15-ago-2026

## Estado: falta pushear el repo y cargar 2 datos. Nada más.

---

## ✅ Hecho

- **Meta**: cuenta desarrollador registrada, app creada, usuario del sistema creado con
  activos y permisos asignados, **token generado** (lo guardaste vos).
- **App Review: NO se requiere.** Era el riesgo grande del plan. Despejado.
- **GitHub**: repo público creado → https://github.com/XzAZER/olivia-stories (vacío)
- **El bot**: escrito y testeado. 42 slots verificados contra el plan, 0 diferencias.

## ⬜ Falta — 3 pasos, ~10 minutos

### 1. Pushear el repo

Abrí **Git Bash** en `C:\Users\YTMAT\Documents\OLIVIA REDES\olivia-stories` y pegá:

```bash
git init
git add .
git commit -m "Bot de historias Olivia"
git branch -M main
git remote add origin https://github.com/XzAZER/olivia-stories.git
git push -u origin main
```

Si pide credenciales: usuario `XzAZER` y un **Personal Access Token** de GitHub
(Settings → Developer settings → Personal access tokens), no tu contraseña.

**Verificá que las placas se sirven** — abrí esto en incógnito:

```
https://raw.githubusercontent.com/XzAZER/olivia-stories/main/placas/grilla.jpg
```

Tenés que ver la imagen. Si pide login, algo quedó privado.

### 2. Cargar la variable RAW_BASE

Quedé a mitad de esto cuando se cortó. Andá a:

**Settings → Secrets and variables → Actions → pestaña Variables → New repository variable**

| Name | Value |
|---|---|
| `RAW_BASE` | `https://raw.githubusercontent.com/XzAZER/olivia-stories/main` |

### 3. Cargar los 2 secrets

**Misma página, pestaña Secrets → New repository secret**

| Name | Value |
|---|---|
| `FB_PAGE_ID` | `555689564301742` |
| `META_ACCESS_TOKEN` | el token que guardaste (empieza con `EAAY...`) |

`IG_USER_ID` no hace falta — el script lo descubre solo.

---

## Después: el test real

**Actions → Historias Olivia → Run workflow**

Primero en seco:
- `slot` = `2026-08-16T11:00`
- `dry_run` = `true`

Si el log muestra el slot y la URL correcta, repetí con `dry_run` = `false`.
Eso publica una historia **de verdad, en ese momento**, en FB e IG.

Mirala en el celular. Si salió bien:
1. Borrá la historia a mano de las dos redes
2. Editá `state.json` y dejalo en `{"publicados": []}`
3. Commiteá ese cambio

A partir de ahí el cron se encarga: domingo 16 a las 11:00 arranca solo.

---

## Si algo falla, pegame el error tal cual

Los sospechosos probables, en orden:

| Error | Causa |
|---|---|
| `(#10) Application does not have permission` | Faltó algún permiso en el token |
| `Media upload has failed` en IG | La raw URL no es pública, o el repo quedó privado |
| `Unsupported get request` | El `FB_PAGE_ID` está mal |
| `Invalid OAuth access token` | El token se copió cortado |
| `No hay ninguna historia para este horario` | Normal fuera de los horarios. Usá `--slot` |

---

## Datos que vas a necesitar

| Cosa | Valor |
|---|---|
| Repo | https://github.com/XzAZER/olivia-stories |
| App de Meta | Olivia Historias Bot — ID `1738265650827335` |
| Usuario del sistema | ID `61593635750216` |
| Página de FB | `555689564301742` |
| Portfolio | `614700221198010` |
| Token vence | ~14-oct-2026 (la campaña termina el 5-sep, no molesta) |

## Recordatorio de seguridad

El token quedó parcialmente visible en una captura de pantalla durante el setup. Está
cortado y no es utilizable así, pero si querés cero ambigüedad: cuando todo funcione,
revocalo y generá uno nuevo. Business Settings → Users → System users → Olivia Historias
Bot → Revoke tokens → Generate token. Después actualizás el secret en GitHub.

## Primera historia

**Domingo 16-ago 11:00** — `docena.jpg` (Promo Docena NUEVA $35.600)

Si el 16 a las 11:05 no salió nada, entrá a la pestaña Actions del repo y mirá el log
de la corrida. Ahí va a estar el motivo.

---

## ⚠️ ATENCIÓN — token.txt

Guardaste el token en:

```
C:\Users\YTMAT\Documents\OLIVIA REDES\token.txt
```

Ese archivo está en la carpeta **padre**, un nivel arriba del repo. Por eso `git add .`
desde dentro de `olivia-stories` no lo va a tocar. Además está en el `.gitignore` como
red de seguridad.

**Pero el repo es PÚBLICO.** Si por cualquier motivo ese archivo termina adentro y se
commitea, el token queda expuesto a todo internet, con permiso para publicar en la página
y en el Instagram de Olivia.

Reglas:

1. **Nunca muevas `token.txt` adentro de `olivia-stories/`.**
2. Después de pegar el token en el secret de GitHub, **borrá `token.txt`**. Ya no lo
   necesitás: GitHub lo guarda encriptado.
3. Antes del primer push, corré `git status` y confirmá que no aparece ningún archivo
   con "token" en el nombre.

Si alguna vez se te escapa un commit con el token: revocalo en Business Settings →
Users → System users → Revoke tokens, y generá uno nuevo. Borrar el commit no alcanza,
GitHub conserva el historial.
