import os
import json
import sys

def main():
    print("========================================================")
    print("      EXPORTADOR DE CATÁLOGO DESDE JSON LOCAL")
    print("========================================================")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Buscar géneros disponibles
    generos_disponibles = []
    for root, dirs, files in os.walk(base_dir):
        if ".venv" in root or ".cache" in root or ".git" in root:
            continue
        if "ringtones.json" in files:
            genero = os.path.basename(root)
            generos_disponibles.append(genero)
            
    if generos_disponibles:
        print(f"[INFO] Géneros disponibles: {', '.join(generos_disponibles)}")
    else:
        print("[INFO] No se encontraron archivos ringtones.json en ninguna carpeta.")
        input("Presiona ENTER para salir...")
        return
        
    print("")
    if len(sys.argv) > 1:
        genero_input = sys.argv[1].strip()
    else:
        genero_input = input("Ingresa el nombre del género (carpeta) que deseas exportar: ").strip()
    
    if not genero_input:
        print("[ERROR] No ingresaste ningún género.")
        if len(sys.argv) <= 1:
            input("Presiona ENTER para salir...")
        return
        
    json_path = os.path.join(base_dir, genero_input, "ringtones.json")
    
    if not os.path.exists(json_path):
        print(f"[ERROR] No se encontró el archivo de canciones para el género: {genero_input}")
        print("Asegúrate de que la carpeta exista y esté bien escrita.")
        input("Presiona ENTER para salir...")
        return

    canciones = []
    
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            
        if data:
            for item in data:
                title = str(item.get("title") or "").strip()
                subtitle = str(item.get("subtitle") or "").strip()
                
                if title:
                    # Formato "Artista - Titulo"
                    canciones.append(f"{subtitle} - {title}" if subtitle and subtitle != "Unknown" else title)
    except Exception as e:
        print(f"[ERROR] Error leyendo {json_path}: {e}")

    if not canciones:
        print(f"[INFO] No se encontraron canciones para el género '{genero_input}'.")
        input("Presiona ENTER para salir...")
        return
        
    output_file = os.path.join(base_dir, f"mis_canciones_{genero_input.replace(' ', '_')}.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"=== CANCIONES EXPORTADAS ({genero_input.upper()}) - TOTAL: {len(canciones)} canciones ===\n\n")
        for c in canciones:
            f.write(f"- {c}\n")
            
    print(f"\n[OK] ¡Exportación exitosa! Se encontraron {len(canciones)} canciones.")
    print(f"[INFO] Guardado en: {output_file}")
    print("[INFO] Abriendo el archivo en Notepad para que lo copies...")
    
    try:
        os.system(f"notepad.exe \"{output_file}\"")
    except:
        pass

if __name__ == "__main__":
    main()
