#!/usr/bin/env python3
"""
Publica las historias de Olivia en Facebook + Instagram.

Ni la API de FB ni la de IG permiten programar historias: publican en el instante.
Por eso este script no "programa" nada - lo dispara el cron de GitHub Actions en el
horario correcto, y el script decide si en ESTE momento le toca publicar algo.

Uso:
    python publish.py              # publica el slot que corresponde a ahora
    python publish.py --dry-run    # muestra que haria, no llama a la API
    python publish.py --check      # verifica que el token funciona, no publica nada
    python publish.py --slot 2026-08-16T11:00   # fuerza un slot puntual (test)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

# --- Config ---------------------------------------------------------------

GRAPH = "https://graph.facebook.com/v21.0"
ART = timezone(timedelta(hours=-3))          # Argentina, sin horario de verano
TOLERANCIA_MIN = 45                          # GH Actions puede atrasarse bajo carga

BASE = os.path.dirname(os.path.abspath(__file__))
SCHEDULE = os.path.join(BASE, "schedule.json")
STATE = os.path.join(BASE, "state.json")

PAGE_ID = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")
TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
RAW_BASE = os.environ.get("RAW_BASE", "").rstrip("/")


def verificar(r):
    """
    raise_for_status() tira el cuerpo de la respuesta, y ahi es donde Meta explica
    QUE esta mal (code 190 = token invalido/expirado, 100 = parametro incorrecto,
    102 = sesion caida, 200 = falta permiso). Sin eso hay que adivinar.
    """
    if not r.ok:
        detalle = r.text[:500] if r.text else "(sin cuerpo)"
        raise RuntimeError(f"HTTP {r.status_code} - {detalle}")
    return r


# --- Estado (evita publicar dos veces si se re-dispara el workflow) --------

def cargar_estado():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"publicados": []}


def guardar_estado(estado):
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(estado, fh, indent=2, ensure_ascii=False)


# --- Seleccion del slot ---------------------------------------------------

def parsear(slot):
    return datetime.strptime(slot["id"], "%Y-%m-%dT%H:%M").replace(tzinfo=ART)


def slot_de_ahora(slots, ahora):
    candidatos = [
        (abs((parsear(s) - ahora).total_seconds()), s)
        for s in slots
        if abs((parsear(s) - ahora).total_seconds()) <= TOLERANCIA_MIN * 60
    ]
    if not candidatos:
        return None
    return min(candidatos, key=lambda par: par[0])[1]


# --- Publicacion ----------------------------------------------------------

def token_de_pagina():
    """
    CRITICO: el token del usuario del sistema NO sirve para publicar como la pagina.
    Facebook devuelve 403. Hay que canjearlo por un token de pagina.
    """
    if not hasattr(token_de_pagina, "_cache"):
        r = requests.get(
            f"{GRAPH}/{PAGE_ID}",
            params={"fields": "access_token", "access_token": TOKEN},
            timeout=30,
        )
        verificar(r)
        pt = r.json().get("access_token")
        if not pt:
            raise RuntimeError(
                "La respuesta no trajo access_token. Revisa que el usuario del "
                "sistema tenga la pagina asignada con la tarea 'Content'."
            )
        token_de_pagina._cache = pt
        print("Token de pagina obtenido.")
    return token_de_pagina._cache


def publicar_facebook(url_imagen):
    pt = token_de_pagina()
    r = requests.post(
        f"{GRAPH}/{PAGE_ID}/photos",
        data={"url": url_imagen, "published": "false", "access_token": pt},
        timeout=60,
    )
    verificar(r)
    photo_id = r.json()["id"]

    r = requests.post(
        f"{GRAPH}/{PAGE_ID}/photo_stories",
        data={"photo_id": photo_id, "access_token": pt},
        timeout=60,
    )
    verificar(r)
    return r.json()


def descubrir_ig_user_id():
    if IG_USER_ID:
        return IG_USER_ID
    r = requests.get(
        f"{GRAPH}/{PAGE_ID}",
        params={"fields": "instagram_business_account", "access_token": TOKEN},
        timeout=30,
    )
    verificar(r)
    cuenta = r.json().get("instagram_business_account")
    if not cuenta:
        raise RuntimeError(
            "La pagina no tiene una cuenta de Instagram profesional vinculada, "
            "o el token no tiene permiso para verla."
        )
    print(f"IG user id descubierto: {cuenta['id']}")
    return cuenta["id"]


def publicar_instagram(url_imagen):
    ig_id = descubrir_ig_user_id()
    r = requests.post(
        f"{GRAPH}/{ig_id}/media",
        data={"image_url": url_imagen, "media_type": "STORIES", "access_token": TOKEN},
        timeout=60,
    )
    verificar(r)
    creation_id = r.json()["id"]

    r = requests.post(
        f"{GRAPH}/{ig_id}/media_publish",
        data={"creation_id": creation_id, "access_token": TOKEN},
        timeout=60,
    )
    verificar(r)
    return r.json()


# --- Chequeo de salud -----------------------------------------------------

def chequeo():
    """Verifica el token SIN publicar nada. Solo llamadas de lectura."""
    print("=== Chequeo de salud ===")
    problemas = []

    faltantes = [
        n for n, v in (("FB_PAGE_ID", PAGE_ID), ("META_ACCESS_TOKEN", TOKEN),
                       ("RAW_BASE", RAW_BASE)) if not v
    ]
    if faltantes:
        print("FALTAN VARIABLES: " + ", ".join(faltantes))
        sys.exit(1)

    # Pistas sobre la forma del token, sin exponerlo.
    print(f"Token: {len(TOKEN)} caracteres, empieza con '{TOKEN[:4]}', "
          f"termina con '{TOKEN[-4:]}'")
    if TOKEN != TOKEN.strip():
        print("AVISO: el token tiene espacios o saltos de linea al principio o al final.")
    if len(TOKEN) < 100:
        print("AVISO: parece corto. Un token de usuario del sistema suele pasar "
              "los 180 caracteres. Puede haberse copiado cortado.")

    # /me dice quien es el token, sin depender de la pagina.
    try:
        r = requests.get(f"{GRAPH}/me", params={"access_token": TOKEN}, timeout=30)
        verificar(r)
        print(f"OK  Identidad del token: {r.json()}")
    except Exception as exc:
        problemas.append(f"identidad: {exc}")
        print(f"FALLA identidad del token: {exc}")

    try:
        token_de_pagina()
        print("OK  Facebook: el token canjea por token de pagina.")
    except Exception as exc:
        problemas.append(f"FB: {exc}")
        print(f"FALLA Facebook: {exc}")

    try:
        ig = descubrir_ig_user_id()
        print(f"OK  Instagram: cuenta vinculada {ig}")
    except Exception as exc:
        problemas.append(f"IG: {exc}")
        print(f"FALLA Instagram: {exc}")

    try:
        with open(SCHEDULE, encoding="utf-8") as fh:
            slots = json.load(fh)["slots"]
        estado = cargar_estado()
        ahora = datetime.now(ART)
        pendientes = [s for s in slots
                      if s["id"] not in estado["publicados"] and parsear(s) > ahora]
        print(f"OK  Grilla: {len(slots)} slots, {len(pendientes)} pendientes a futuro.")
        if pendientes:
            prox = min(pendientes, key=parsear)
            print(f"    Proxima: {prox['id']} -> {prox['placa']}")
    except Exception as exc:
        problemas.append(f"Grilla: {exc}")
        print(f"FALLA Grilla: {exc}")

    if problemas:
        sys.exit("CHEQUEO FALLIDO")
    print("=== Todo OK. El bot puede publicar. ===")


# --- Main -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--slot", help="ID de slot puntual, ej 2026-08-16T11:00")
    args = ap.parse_args()

    if args.check:
        chequeo()
        return

    with open(SCHEDULE, encoding="utf-8") as fh:
        slots = json.load(fh)["slots"]

    ahora = datetime.now(ART)
    print(f"Ahora en Argentina: {ahora:%Y-%m-%d %H:%M}")

    if args.slot:
        slot = next((s for s in slots if s["id"] == args.slot), None)
        if slot is None:
            sys.exit(f"No existe el slot {args.slot}")
    else:
        slot = slot_de_ahora(slots, ahora)

    if slot is None:
        print("No hay ninguna historia para este horario. Nada que hacer.")
        return

    estado = cargar_estado()
    if slot["id"] in estado["publicados"]:
        print(f"{slot['id']} ya se publico antes. Salteando para no duplicar.")
        return

    url_imagen = f"{RAW_BASE}/placas/{slot['placa']}"
    print(f"Slot {slot['id']} -> {slot['placa']}")
    print(f"URL: {url_imagen}")

    if args.dry_run:
        print("[dry-run] No se llamo a la API.")
        return

    faltantes = [
        n for n, v in (("FB_PAGE_ID", PAGE_ID), ("META_ACCESS_TOKEN", TOKEN),
                       ("RAW_BASE", RAW_BASE)) if not v
    ]
    if faltantes:
        sys.exit("Faltan variables de entorno: " + ", ".join(faltantes))

    errores = []

    try:
        print("Facebook:", publicar_facebook(url_imagen))
    except Exception as exc:
        errores.append(f"FB: {exc}")
        print(f"ERROR Facebook: {exc}", file=sys.stderr)

    try:
        print("Instagram:", publicar_instagram(url_imagen))
    except Exception as exc:
        errores.append(f"IG: {exc}")
        print(f"ERROR Instagram: {exc}", file=sys.stderr)

    if len(errores) < 2:
        estado["publicados"].append(slot["id"])
        guardar_estado(estado)

    if errores:
        sys.exit("Fallos: " + " | ".join(errores))

    print("OK - publicada en FB e IG.")


if __name__ == "__main__":
    main()
