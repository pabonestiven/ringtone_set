Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " INICIANDO SUBIDA AUTOMATICA A GITHUB POR LOTES" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Configurando el limite de memoria de Git para archivos pesados..." -ForegroundColor DarkGray
git config --global http.postBuffer 524288000

$availableFolders = Get-ChildItem -Directory | Where-Object { Test-Path (Join-Path $_.FullName "audios") } | Select-Object -ExpandProperty Name

if ($availableFolders.Count -eq 0) {
    Write-Host "No se encontraron carpetas con audios." -ForegroundColor Red
} else {
    foreach ($folder in $availableFolders) {
        Write-Host "`n---> Evaluando carpeta: $folder" -ForegroundColor Yellow
        
        # Agregamos todo en esta carpeta (nuevos, modificados y eliminados)
        git add --all "$folder/"
        
        # Verificamos si realmente hay cambios nuevos en esta carpeta
        $status = git status --porcelain "$folder/"
        
        if ($status) {
            Write-Host "  -> Cambios detectados. Guardando (commit)..."
            git commit -m "Agregando/actualizando audios y datos de $folder" | Out-Null
            
            $maxRetries = 3
            $retryCount = 0
            $pushSuccess = $false
            
            while ($retryCount -lt $maxRetries -and -not $pushSuccess) {
                Write-Host "  -> Subiendo a GitHub (push) [Intento $($retryCount + 1)/$maxRetries]..." -ForegroundColor Magenta
                git push
                
                if ($LASTEXITCODE -eq 0) {
                    $pushSuccess = $true
                    Write-Host "  [OK] $folder subido con exito." -ForegroundColor Green
                } else {
                    $retryCount++
                    Write-Host "  [ADVERTENCIA] Fallo la subida de $folder. Reintentando..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 5
                }
            }
            
            if (-not $pushSuccess) {
                Write-Host "`n[ERROR CRITICO] No se pudo subir $folder tras $maxRetries intentos." -ForegroundColor Red
                Write-Host "Para evitar que se acumulen demasiados archivos y falle por limite de tamano, el script se detendra aqui." -ForegroundColor Red
                Write-Host "Los archivos de $folder ya estan guardados localmente." -ForegroundColor Yellow
                Write-Host "Revisa tu conexion a internet y vuelve a ejecutar este script mas tarde." -ForegroundColor Yellow
                Write-Host "Presiona Enter para salir..."
                Read-Host
                exit
            }
        } else {
            Write-Host "  [OK] No hay archivos nuevos o modificados en $folder. Saltando." -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n---> Verificando si hay otros archivos sueltos (scripts, configuraciones)..." -ForegroundColor Yellow
git add .
$statusFinal = git status --porcelain
if ($statusFinal) {
    Write-Host "  -> Archivos extra detectados. Subiendo..."
    git commit -m "Actualizacion de archivos generales de configuracion" | Out-Null
    git push
    Write-Host "  [OK] Archivos generales subidos." -ForegroundColor Green
} else {
    Write-Host "  [OK] Todo esta al dia." -ForegroundColor DarkGray
}

Write-Host "`n=================================================" -ForegroundColor Cyan
Write-Host " TODAS LAS SUBIDAS HAN TERMINADO" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Presiona Enter para salir..."
Read-Host
