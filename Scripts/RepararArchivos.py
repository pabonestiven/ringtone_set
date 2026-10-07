import os
import json

def fix_text(text):
    if not isinstance(text, str): return text
    try:
        # Intenta revertir la lectura incorrecta de ANSI (cp1252) sobre bytes UTF-8
        return text.encode('cp1252').decode('utf-8')
    except:
        return text

def fix_dict(d):
    for k, v in list(d.items()):
        if isinstance(v, str):
            d[k] = fix_text(v)
        elif isinstance(v, dict):
            fix_dict(v)
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], str):
                    v[i] = fix_text(v[i])
                elif isinstance(v[i], dict):
                    fix_dict(v[i])

print("=========================================")
print("REPARANDO ARCHIVOS JSON CORRUPTOS")
print("=========================================\n")

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for root, dirs, files in os.walk(base_dir):
    if 'ringtones.json' in files:
        path = os.path.join(root, 'ringtones.json')
        print(f"Analizando: {path}")
        with open(path, 'r', encoding='utf-8-sig') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"  [ERROR] No se pudo leer {path}: {e}")
                continue
        
        needs_save = False
        
        # Desempaquetar multiples "value" anidados (puede haber varios)
        while isinstance(data, dict) and 'value' in data:
            data = data['value']
            needs_save = True
            
        # A veces el array principal contiene UN elemento que a su vez es un dict con 'value'
        while isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and 'value' in data[0]:
            data = data[0]['value']
            needs_save = True
        
        if isinstance(data, list):
            flat_items = []
            def extract_items(lst):
                for item in lst:
                    if isinstance(item, dict) and 'value' in item:
                        if isinstance(item['value'], list):
                            extract_items(item['value'])
                    elif isinstance(item, dict) and 'id' in item:
                        fix_dict(item)
                        flat_items.append(item)
            
            extract_items(data)
            
            # Limpiar duplicados por si acaso
            seen_paths = set()
            clean_list = []
            for item in flat_items:
                path_str = item.get('audioPath', '')
                if path_str not in seen_paths:
                    seen_paths.add(path_str)
                    clean_list.append(item)
            
            # Ordenar por ID para mantener limpieza
            def get_id(x):
                try: return int(x.get('id', 0))
                except: return 0
            clean_list.sort(key=get_id)
            
            # Siempre guardamos para forzar correccion de acentos (Ã‰l -> Él)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(clean_list, f, indent=4, ensure_ascii=False)
            print(f"  -> REPARADO y guardado limpiamente con {len(clean_list)} canciones.\n")
        else:
            print(f"  -> No se pudo determinar el formato de este archivo.\n")

print("PROCESO TERMINADO. Ya puedes volver a usar Automatizador.ps1 de forma segura.")
