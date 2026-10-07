"""
╔══════════════════════════════════════════════════════════╗
║         AIRTABLE DATABASE CHECKER - DIAGNÓSTICO          ║
║  Verifica conexión, permisos y estructura de datos       ║
╚══════════════════════════════════════════════════════════╝

Uso:
    python airtable_checker.py

    O pasando credenciales por variables de entorno:
        set AIRTABLE_TOKEN=patXXXXXX
        set AIRTABLE_TABLE_ID=tblXXXXXX
        set AIRTABLE_BASE_ID=appXXXXXX
        python airtable_checker.py
"""

import os
import sys
import json
import requests
from datetime import datetime

# ─────────────────────────────────────────────
#   CONFIGURACIÓN — Edita aquí si prefieres
#   no ingresar los datos manualmente cada vez
# ─────────────────────────────────────────────
AIRTABLE_TOKEN   = os.getenv("AIRTABLE_TOKEN", "")      # Personal Access Token (pat...)
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")    # ID de la base          (app...)
AIRTABLE_TABLE_ID= os.getenv("AIRTABLE_TABLE_ID", "")   # ID o nombre de la tabla (tbl...)

BASE_URL = "https://api.airtable.com/v0"

# ─────────────────────────────────────────────
#   UTILIDADES DE CONSOLA
# ─────────────────────────────────────────────

def titulo(texto):
    sep = "─" * 56
    print(f"\n{sep}")
    print(f"  {texto}")
    print(sep)

def ok(msg):    print(f"  ✅  {msg}")
def error(msg): print(f"  ❌  {msg}")
def info(msg):  print(f"  ℹ️   {msg}")
def warn(msg):  print(f"  ⚠️   {msg}")

def separador(): print("  " + "·" * 52)

# ─────────────────────────────────────────────
#   SOLICITAR CREDENCIALES INTERACTIVAMENTE
# ─────────────────────────────────────────────

def seleccionar_tabla_interactivo():
    """Llama a la API Meta para listar tablas y deja escoger por número."""
    global AIRTABLE_TABLE_ID

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
    except Exception as e:
        error(f"No se pudo conectar para listar tablas: {e}")
        sys.exit(1)

    if resp.status_code != 200:
        error(f"Error al obtener tablas (HTTP {resp.status_code}): {resp.text[:200]}")
        sys.exit(1)

    tablas = resp.json().get("tables", [])
    if not tablas:
        error("La base no tiene tablas o el token no tiene permisos de lectura de esquema.")
        sys.exit(1)

    print("\n  📋 Tablas disponibles en la base:")
    for i, t in enumerate(tablas, 1):
        print(f"     [{i}] {t.get('name','?')}  —  id: {t.get('id','?')}")

    while True:
        try:
            eleccion = input(f"\n  Elige el número de la tabla [1-{len(tablas)}]: ").strip()
            idx = int(eleccion) - 1
            if 0 <= idx < len(tablas):
                AIRTABLE_TABLE_ID = tablas[idx]["id"]
                ok(f"Tabla seleccionada: '{tablas[idx]['name']}' ({AIRTABLE_TABLE_ID})")
                break
            else:
                warn(f"Número fuera de rango. Ingresa entre 1 y {len(tablas)}.")
        except ValueError:
            warn("Ingresa solo el número de la tabla.")


def pedir_credenciales():
    global AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID

    print("\n🔐  Introduce tus credenciales de Airtable")
    print("    (Presiona Enter para usar el valor ya configurado)\n")

    if not AIRTABLE_TOKEN:
        AIRTABLE_TOKEN = input("  Personal Access Token (patXXX...): ").strip()
    else:
        info(f"Token cargado desde entorno: {AIRTABLE_TOKEN[:12]}...")

    if not AIRTABLE_BASE_ID:
        AIRTABLE_BASE_ID = input("  Base ID (appXXX...): ").strip()
    else:
        info(f"Base ID desde entorno: {AIRTABLE_BASE_ID}")

    if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
        error("Faltan el Token o el Base ID. Abortando.")
        sys.exit(1)

    # Table ID es OPCIONAL — si no se tiene, se listan las disponibles
    if not AIRTABLE_TABLE_ID:
        warn("No se proporcionó Table ID. Consultando la base para listar tablas...")
        seleccionar_tabla_interactivo()
    else:
        info(f"Table ID desde entorno: {AIRTABLE_TABLE_ID}")

# ─────────────────────────────────────────────
#   HEADERS COMUNES
# ─────────────────────────────────────────────

def get_headers():
    return {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type":  "application/json"
    }

# ─────────────────────────────────────────────
#   PRUEBA 1 — Autenticación y acceso a la base
# ─────────────────────────────────────────────

def verificar_autenticacion():
    titulo("PRUEBA 1 · Autenticación y acceso a la base")

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
    except requests.exceptions.ConnectionError:
        error("Sin conexión a Internet o DNS fallido.")
        return False
    except requests.exceptions.Timeout:
        error("Tiempo de espera agotado (15 s).")
        return False

    info(f"HTTP {resp.status_code} — {url}")

    if resp.status_code == 200:
        data = resp.json()
        tablas = data.get("tables", [])
        ok(f"Autenticación exitosa. La base tiene {len(tablas)} tabla(s):")
        for t in tablas:
            print(f"      • {t.get('name', '?')}  (id: {t.get('id', '?')})")
        return True

    elif resp.status_code == 401:
        error("Token inválido o expirado. Revisa tu Personal Access Token.")
    elif resp.status_code == 403:
        error("Sin permisos sobre esta base. Verifica scopes del token (data.records:read, schema.bases:read).")
    elif resp.status_code == 404:
        error("Base ID no encontrado. ¿Está bien escrito el appXXXXXX?")
    else:
        error(f"Error inesperado: {resp.text[:300]}")

    return False

# ─────────────────────────────────────────────
#   PRUEBA 2 — Estructura de la tabla (campos)
# ─────────────────────────────────────────────

def verificar_estructura_tabla():
    titulo("PRUEBA 2 · Estructura de la tabla (campos)")

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    resp = requests.get(url, headers=get_headers(), timeout=15)

    if resp.status_code != 200:
        warn("No se pudo obtener la estructura (prueba anterior falló).")
        return []

    tablas = resp.json().get("tables", [])
    tabla_target = None

    for t in tablas:
        if t.get("id") == AIRTABLE_TABLE_ID or t.get("name") == AIRTABLE_TABLE_ID:
            tabla_target = t
            break

    if not tabla_target:
        warn(f"Tabla '{AIRTABLE_TABLE_ID}' no encontrada en la base.")
        warn("Prueba con el ID exacto (tblXXXXXX) o con el nombre exacto.")
        return []

    ok(f"Tabla encontrada: '{tabla_target['name']}' ({tabla_target['id']})")
    campos = tabla_target.get("fields", [])
    info(f"Total de campos: {len(campos)}")
    separador()
    print(f"  {'#':<4} {'Nombre':<30} {'Tipo'}")
    separador()
    for i, campo in enumerate(campos, 1):
        print(f"  {i:<4} {campo.get('name','?'):<30} {campo.get('type','?')}")

    return [c.get("name") for c in campos]

# ─────────────────────────────────────────────
#   PRUEBA 3 — Lectura de registros reales
# ─────────────────────────────────────────────

def verificar_registros(campos_conocidos):
    titulo("PRUEBA 3 · Lectura de registros de la tabla")

    url = f"{BASE_URL}/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    params = {"maxRecords": 5, "pageSize": 5}

    try:
        resp = requests.get(url, headers=get_headers(), params=params, timeout=15)
    except Exception as e:
        error(f"Excepción al consultar registros: {e}")
        return

    info(f"HTTP {resp.status_code}")

    if resp.status_code != 200:
        error(f"Error al leer registros: {resp.text[:400]}")
        return

    data = resp.json()
    registros = data.get("records", [])
    offset   = data.get("offset")

    if not registros:
        warn("La tabla está vacía o no tiene registros visibles con este token.")
        return

    ok(f"Se recibieron {len(registros)} registro(s) (máximo solicitado: 5)")
    if offset:
        info("Hay más registros disponibles (offset presente).")

    separador()
    for i, rec in enumerate(registros, 1):
        print(f"\n  📄 Registro #{i}  —  id: {rec.get('id')}")
        print(f"     Creado: {rec.get('createdTime', 'N/A')}")
        fields = rec.get("fields", {})
        if fields:
            for campo, valor in fields.items():
                # Truncar valores muy largos
                val_str = str(valor)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                print(f"     • {campo}: {val_str}")
        else:
            warn("  Sin campos visibles en este registro.")

# ─────────────────────────────────────────────
#   PRUEBA 4 — Velocidad de respuesta
# ─────────────────────────────────────────────

def verificar_latencia():
    titulo("PRUEBA 4 · Latencia de la API")

    url = f"{BASE_URL}/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    params = {"maxRecords": 1}

    tiempos = []
    intentos = 3

    for i in range(1, intentos + 1):
        t_inicio = datetime.now()
        try:
            resp = requests.get(url, headers=get_headers(), params=params, timeout=15)
            t_fin = datetime.now()
            ms = int((t_fin - t_inicio).total_seconds() * 1000)
            tiempos.append(ms)
            estado = "✅" if resp.status_code == 200 else "❌"
            print(f"  {estado}  Intento {i}: {ms} ms  (HTTP {resp.status_code})")
        except Exception as e:
            print(f"  ❌  Intento {i}: Error — {e}")

    if tiempos:
        promedio = sum(tiempos) / len(tiempos)
        separador()
        info(f"Latencia promedio: {promedio:.0f} ms")
        if promedio < 500:
            ok("Conexión rápida. Sin problemas de red detectados.")
        elif promedio < 1500:
            warn("Latencia moderada. Podría ser mejorable.")
        else:
            warn("Latencia alta (>1500 ms). Puede afectar la experiencia.")

# ─────────────────────────────────────────────
#   RESUMEN FINAL
# ─────────────────────────────────────────────

def resumen_final(exito_auth):
    titulo("RESUMEN DEL DIAGNÓSTICO")
    print(f"\n  Base ID  : {AIRTABLE_BASE_ID}")
    print(f"  Tabla    : {AIRTABLE_TABLE_ID}")
    print(f"  Token    : {AIRTABLE_TOKEN[:12]}...{AIRTABLE_TOKEN[-4:]}\n")

    if exito_auth:
        ok("La base de datos Airtable está accesible y respondiendo.")
        print("\n  💡 Próximos pasos sugeridos:")
        print("     • Verifica que los campos mostrados coincidan con tu modelo de datos.")
        print("     • Si faltan registros, revisa los filtros de vista en Airtable.")
        print("     • Para producción, usa variables de entorno para el token.")
    else:
        error("No se pudo verificar la base de datos. Revisa los errores arriba.")
        print("\n  🔧 Checklist de solución:")
        print("     1. ¿El token empieza con 'pat'? (Personal Access Token, no API Key legacy)")
        print("     2. ¿El token tiene scopes: data.records:read y schema.bases:read?")
        print("     3. ¿El Base ID empieza con 'app'?")
        print("     4. ¿El Table ID empieza con 'tbl' o usaste el nombre exacto?")
        print("     5. ¿El token tiene acceso a esa base específica?")

    print(f"\n  Diagnóstico completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ─────────────────────────────────────────────
#   PUNTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 58)
    print("   🛢️  AIRTABLE DATABASE CHECKER  —  Diagnóstico Completo")
    print("═" * 58)

    pedir_credenciales()

    exito = verificar_autenticacion()

    campos = []
    if exito:
        campos = verificar_estructura_tabla()
        verificar_registros(campos)
        verificar_latencia()

    resumen_final(exito)
