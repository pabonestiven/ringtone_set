import os
import requests
import sys
import json

# 1. Intentar leer desde las variables de entorno (Inyectadas por la UI)
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.environ.get("AIRTABLE_TABLE_ID")
TARGET_FOLDER = os.environ.get("TARGET_FOLDER", "base")
COL_ARTIST = os.environ.get("COL_ARTIST", "Subtitle")
COL_TITLE = os.environ.get("COL_TITLE", "Title")
COL_AUDIO = os.environ.get("COL_AUDIO", "Ringtone")
COL_ICON = os.environ.get("COL_ICON", "Icon")

# 2. Si faltan datos, intentar leer desde config.py (Legacy mode)
if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID or not AIRTABLE_TABLE_ID:
    try:
        import config
        if not AIRTABLE_TOKEN: AIRTABLE_TOKEN = getattr(config, "AIRTABLE_TOKEN", None)
        if not AIRTABLE_BASE_ID: AIRTABLE_BASE_ID = getattr(config, "AIRTABLE_BASE_ID", None)
        if not AIRTABLE_TABLE_ID: AIRTABLE_TABLE_ID = getattr(config, "AIRTABLE_TABLE_ID", None)
    except ImportError:
        pass


def descargar_archivo(url, destino):
    try:
        if os.path.exists(destino):
            print(f"  [OMITIDO] Ya existe: {os.path.basename(destino)}")
            return True
            
        print(f"  [DESCARGANDO] {os.path.basename(destino)}...")
        respuesta = requests.get(url, stream=True, timeout=30)
        respuesta.raise_for_status()
        
        with open(destino, 'wb') as f:
            for chunk in respuesta.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  [OK] Guardado: {os.path.basename(destino)}")
        return True
    except Exception as e:
        print(f"  [ERROR] Al descargar {url}: {e}")
        return False

def main():
    print("========================================================")
    print("      DESCARGADOR DE CANCIONES (MP3) DESDE AIRTABLE")
    print("========================================================")
    
    if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID or not AIRTABLE_TABLE_ID:
        print("[ERROR] Faltan credenciales de Airtable en config.py.")
        sys.exit(1)
        
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    
    # Carpeta donde se guardarán los MP3 y el JSON final
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta_destino = os.path.join(base_dir, TARGET_FOLDER)
    carpeta_audios = os.path.join(carpeta_destino, "audios")
    carpeta_imagenes = os.path.join(carpeta_destino, "images")
    json_path = os.path.join(carpeta_destino, "ringtones.json")
    
    os.makedirs(carpeta_audios, exist_ok=True)
    os.makedirs(carpeta_imagenes, exist_ok=True)
    
    print(f"[INFO] Inyectando directamente en: {os.path.abspath(carpeta_destino)}")
    print(f"[INFO] Columnas mapeadas -> Artista: '{COL_ARTIST}', Titulo: '{COL_TITLE}', Audio: '{COL_AUDIO}', Icon: '{COL_ICON}'")
    
    # Cargar JSON existente para max_id y evitar duplicados
    db_json = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                db_json = json.load(f)
        except Exception:
            db_json = []
            
    # Función para obtener el max ID actual
    def get_next_id():
        if not db_json: return 1
        max_id = 0
        for item in db_json:
            try:
                curr_id = int(item.get("id", 0))
                if curr_id > max_id: max_id = curr_id
            except ValueError:
                pass
        return max_id + 1

    # Verificar si una cancion ya existe en el JSON
    def exists_in_json(title, subtitle):
        for item in db_json:
            if item.get("title", "").lower() == title.lower() and item.get("subtitle", "").lower() == subtitle.lower():
                return True
        return False
    
    total_descargados = 0
    total_omitidos = 0
    total_errores = 0
    
    offset = None
    try:
        while True:
            params = {"view": "Grid view"}
            if offset:
                params["offset"] = offset
                
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code != 200:
                print(f"[ERROR] Al consultar Airtable (HTTP {response.status_code}): {response.text}")
                sys.exit(1)
            
            data = response.json()
            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                title = str(fields.get(COL_TITLE) or "").strip()
                subtitle = str(fields.get(COL_ARTIST) or "").strip()
                ringtones = fields.get(COL_AUDIO, [])
                iconos = fields.get(COL_ICON, [])
                
                # Armar el nombre del archivo si es posible
                if title and subtitle and subtitle != "Desconocido" and subtitle != "Unknown":
                    nombre_base = f"{subtitle} - {title}"
                elif title:
                    nombre_base = title
                else:
                    nombre_base = f"Cancion_{rec.get('id')}"
                
                # Limpiar caracteres inválidos
                caracteres_invalidos = '<>:"/\\|?*'
                for char in caracteres_invalidos:
                    nombre_base = nombre_base.replace(char, '')
                    
                nombre_base_kebab = nombre_base.lower().replace(" ", "-")
                
                if not ringtones:
                    if title or subtitle:
                        print(f"[AVISO] '{nombre_base}' no tiene un archivo adjunto en la columna '{COL_AUDIO}'.")
                    continue
                    
                if exists_in_json(title, subtitle):
                    print(f"  [OMITIDO] '{nombre_base}' ya está registrado en el JSON.")
                    total_omitidos += 1
                    continue
                    
                # Descargar la imagen si existe
                poster_path_str = ""
                if iconos and isinstance(iconos, list):
                    img_file = iconos[0]
                    img_url = img_file.get("url")
                    img_name = img_file.get("filename", "")
                    if img_url:
                        img_ext = os.path.splitext(img_name)[1] if img_name else ".jpg"
                        nombre_imagen = f"{nombre_base_kebab}{img_ext}"
                        ruta_imagen = os.path.join(carpeta_imagenes, nombre_imagen)
                        
                        # Evitar imprimir en consola descargas si ya existe para no saturar
                        if not os.path.exists(ruta_imagen):
                            exito_img = descargar_archivo(img_url, ruta_imagen)
                            if exito_img: poster_path_str = f"images/{nombre_imagen}"
                        else:
                            poster_path_str = f"images/{nombre_imagen}"
                            
                # Descargar cada archivo adjunto (normalmente solo hay 1)
                for archivo in ringtones:
                    file_url = archivo.get("url")
                    if not file_url: continue
                        
                    nombre_archivo = f"{nombre_base_kebab}.mp3"
                    ruta_destino = os.path.join(carpeta_audios, nombre_archivo)
                    
                    exito = descargar_archivo(file_url, ruta_destino)
                    if exito:
                        # Añadir al JSON
                        nuevo_id = str(get_next_id())
                        nueva_cancion = {
                            "id": nuevo_id,
                            "title": title or "Desconocido",
                            "subtitle": subtitle or "Desconocido",
                            "audioPath": f"audios/{nombre_archivo}",
                            "posterPath": poster_path_str
                        }
                        db_json.append(nueva_cancion)
                        
                        # Guardar inmediatamente para no perder datos si hay error
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(db_json, f, indent=4, ensure_ascii=False)
                            
                        print(f"  [+] Registrado en JSON con ID: {nuevo_id}")
                        total_descargados += 1
                    else:
                        total_errores += 1
                        
            offset = data.get("offset")
            if not offset:
                break
            
    except Exception as e:
        print(f"[ERROR] Error de conexion o ejecucion: {e}")
        sys.exit(1)
        
    print("========================================================")
    print(f"[RESUMEN] Proceso completado.")
    print(f" - Archivos procesados/descargados: {total_descargados}")
    print(f" - Errores de descarga: {total_errores}")
    print("========================================================")

if __name__ == "__main__":
    main()
