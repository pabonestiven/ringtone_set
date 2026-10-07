import os
import subprocess
import sys
import time

def print_out(msg):
    print(msg)
    sys.stdout.flush()

def run_command(cmd, cwd=None, hide_output=False):
    """Ejecuta un comando y retorna su output y codigo de salida"""
    try:
        if sys.platform == "win32":
            # Usar shell en Windows para que reconozca los binarios globales
            result = subprocess.run(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        else:
            result = subprocess.run(cmd, cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
        if not hide_output and result.stdout:
            print_out(result.stdout)
            
        return result.returncode, result.stdout
    except Exception as e:
        print_out(f"[ERROR EXCEPCION] {str(e)}")
        return 1, str(e)

def main():
    print_out("=================================================")
    print_out(" INICIANDO SUBIDA AUTOMATICA A GITHUB POR LOTES")
    print_out("=================================================")
    
    # 1. Configurar limites de git
    print_out("Configurando el limite de memoria de Git para archivos pesados...")
    run_command("git config --global http.postBuffer 524288000", hide_output=True)
    
    # 2. Verificacion global rapida
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _, out_global = run_command("git status --porcelain", cwd=base_dir, hide_output=True)
    if not out_global or not out_global.strip():
        print_out("\n[OK] El repositorio esta completamente al dia. No hay ningun cambio para subir.")
        print_out("\n=================================================")
        print_out(" PROCESO FINALIZADO SIN CAMBIOS")
        print_out("=================================================")
        sys.exit(0)
    
    # 3. Descubrir carpetas que tienen un subdirectorio "audios"
    carpetas_validas = []
    
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            if os.path.isdir(os.path.join(item_path, "audios")):
                carpetas_validas.append(item)
                
    if not carpetas_validas:
        print_out("No se encontraron carpetas con audios en el repositorio.")
    else:
        for folder in carpetas_validas:
            print_out(f"\n---> Evaluando carpeta: {folder}")
            
            # Agregamos todo en esta carpeta
            run_command(f'git add --all "{folder}/"', cwd=base_dir, hide_output=True)
            
            # Verificamos si realmente hay cambios nuevos en esta carpeta
            code, out = run_command(f'git status --porcelain "{folder}/"', cwd=base_dir, hide_output=True)
            
            if out and out.strip():
                print_out("  -> Cambios detectados. Guardando (commit)...")
                run_command(f'git commit -m "Agregando/actualizando audios y datos de {folder}"', cwd=base_dir, hide_output=True)
                
                max_retries = 3
                retry_count = 0
                push_success = False
                
                while retry_count < max_retries and not push_success:
                    print_out(f"  -> Subiendo a GitHub (push) [Intento {retry_count + 1}/{max_retries}]...")
                    push_code, push_out = run_command("git push", cwd=base_dir, hide_output=False)
                    
                    if push_code == 0:
                        push_success = True
                        print_out(f"  [OK] {folder} subido con exito.")
                    else:
                        retry_count += 1
                        print_out(f"  [ADVERTENCIA] Fallo la subida de {folder}. Reintentando...")
                        time.sleep(5)
                        
                if not push_success:
                    print_out(f"\n[ERROR CRITICO] No se pudo subir {folder} tras {max_retries} intentos.")
                    print_out("Para evitar fallos acumulativos, el script se detendra aqui.")
                    print_out("Los archivos ya estan guardados localmente.")
                    sys.exit(1)
            else:
                print_out(f"  [OK] No hay archivos nuevos o modificados en {folder}. Saltando.")

    print_out("\n---> Verificando si hay otros archivos sueltos (scripts, configuraciones)...")
    run_command("git add .", cwd=base_dir, hide_output=True)
    code_final, out_final = run_command("git status --porcelain", cwd=base_dir, hide_output=True)
    
    if out_final and out_final.strip():
        print_out("  -> Archivos extra detectados. Subiendo...")
        run_command('git commit -m "Actualizacion de archivos generales de configuracion"', cwd=base_dir, hide_output=True)
        run_command("git push", cwd=base_dir, hide_output=False)
        print_out("  [OK] Archivos generales subidos.")
    else:
        print_out("  [OK] Todo esta al dia.")
        
    print_out("\n=================================================")
    print_out(" TODAS LAS SUBIDAS HAN TERMINADO CON EXITO")
    print_out("=================================================")

    # 4. Disparar purga de cache CDN automatica
    try:
        import purgar_cdn
        print_out("\n>>> DISPARANDO PURGA AUTOMATICA DE CACHE CDN >>>\n")
        purgar_cdn.purge_cdn()
    except Exception as e:
        print_out(f"[AVISO] No se pudo ejecutar la purga automatica: {str(e)}")

if __name__ == "__main__":
    main()
