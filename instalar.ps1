# Instala y configura dam en Windows.
# Uso: doble clic en instalar.cmd, o desde PowerShell:
#   powershell -ExecutionPolicy Bypass -File instalar.ps1
# Se puede ejecutar todas las veces que quieras: lo que ya está hecho se salta.
# (Guardado en UTF-8 con BOM para que Windows PowerShell 5 lea bien las tildes.)

$ErrorActionPreference = 'Continue'   # los fallos de git/uv se comprueban con $LASTEXITCODE
Set-Location $PSScriptRoot            # trabaja siempre desde la carpeta del repositorio
$PathOriginal = $env:Path             # para saber después si tu terminal ya encuentra «dam»

function Paso($texto)  { Write-Host ""; Write-Host "==> $texto" }
function Ok($texto)    { Write-Host "    [ok] $texto" }
function Aviso($texto) { Write-Host "    [!] $texto" -ForegroundColor Yellow }
function Parar($texto) { Aviso $texto; exit 1 }
function Tiene($programa) { [bool](Get-Command $programa -ErrorAction SilentlyContinue) }

# 1. git -------------------------------------------------------------------
Paso "Compruebo git"
if (-not (Tiene git)) {
    Parar "No tienes git. Instálalo (winget install --id Git.Git -e) y vuelve a ejecutar este script."
}
Ok (git --version)

# 2. uv --------------------------------------------------------------------
Paso "Compruebo uv"
$env:Path = "$HOME\.local\bin;$env:Path"   # aquí lo deja el instalador oficial
if (-not (Tiene uv)) {
    Write-Host "    No está instalado: lo descargo del instalador oficial (https://astral.sh/uv)"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if (-not (Tiene uv)) { Parar "No he podido instalar uv." }
}
Ok (uv --version)

# 3. Dependencias y comando dam --------------------------------------------
Paso "Instalo las dependencias (uv descarga Python 3.12 si hace falta)"
uv sync
if ($LASTEXITCODE -ne 0) { Parar "uv sync ha fallado (mira el mensaje de arriba)." }

Paso "Instalo el comando dam para todo el sistema"
uv tool install --editable . --force
if ($LASTEXITCODE -ne 0) { Parar "No he podido instalar el comando dam." }
$CarpetaBin = (uv tool dir --bin).Trim()
if (($PathOriginal -split ';') -contains $CarpetaBin) {
    Ok "Tu terminal ya encuentra los comandos de $CarpetaBin"
} else {
    uv tool update-shell
    Aviso "Al terminar, cierra esta terminal y abre otra para que «dam» funcione."
}

# 4. Configuración ---------------------------------------------------------
Paso "Configuración de acciones"
$Config = Join-Path $HOME ".config\dam\acciones.json"
if ((Test-Path $Config) -and ((Get-FileHash acciones.json).Hash -eq (Get-FileHash $Config).Hash)) {
    Ok "Ya tienes $Config y está al día"
} elseif (Test-Path $Config) {
    # Si es de una instalación vieja, dam seguiría usando las acciones viejas
    Aviso "Tu $Config no es igual que la del repo (puede que sea de una instalación vieja)."
    $respuesta = Read-Host "    ¿La cambio por la nueva? Guardo una copia de la tuya [s/N]"
    if ($respuesta -eq 's') {
        $copia = "$Config.antes-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $Config $copia
        Copy-Item acciones.json $Config -Force
        Ok "Puesta la nueva. La tuya está en $copia"
    } else {
        Aviso "No la toco: dam seguirá usando la tuya."
    }
} else {
    New-Item -ItemType Directory -Force (Split-Path $Config) | Out-Null
    Copy-Item acciones.json $Config
    Ok "Copiado acciones.json a $Config (así dam funciona desde cualquier carpeta)"
}

# 4b. Autocompletado con TAB -----------------------------------------------
# No uso «dam --install-completion»: cambiaría la política de PowerShell a Unrestricted
# y añadiría el script al perfil cada vez que lo ejecutaras.
Paso "Activo el autocompletado con TAB"
# La política de una terminal NORMAL: este script corre con -ExecutionPolicy Bypass (ámbito
# Process), así que Get-ExecutionPolicy a secas diría siempre «Bypass». Miro el resto de ámbitos
# en el orden en que manda Windows; si ninguno está definido, Windows usa Restricted.
$Politica = 'Restricted'
foreach ($Ambito in 'MachinePolicy', 'UserPolicy', 'CurrentUser', 'LocalMachine') {
    $p = Get-ExecutionPolicy -Scope $Ambito
    if ($p -ne 'Undefined') { $Politica = $p; break }
}
if ($Politica -eq 'Restricted' -or $Politica -eq 'AllSigned') {
    Aviso "PowerShell no deja cargar scripts (política $Politica), así que el TAB no funcionaría."
    Aviso "Si lo quieres, ejecuta una vez:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
    Aviso "y vuelve a lanzar este instalador. (RemoteSigned deja ejecutar tus scripts, no los descargados.)"
} else {
    $ScriptTab = Join-Path $HOME ".config\dam\completado.ps1"
    # Con esta variable, dam no ejecuta nada: solo escribe el script de autocompletado
    $env:_DAM_COMPLETE = "source_powershell"
    $Texto = & (Join-Path $CarpetaBin "dam.exe")
    Remove-Item Env:_DAM_COMPLETE
    if ($LASTEXITCODE -ne 0 -or -not $Texto) {
        Aviso "No he podido generar el autocompletado."
    } else {
        Set-Content -Path $ScriptTab -Value ($Texto -join "`r`n") -Encoding UTF8
        $Linea = ". `"$ScriptTab`"  # autocompletado de dam (lo añadió instalar.ps1)"
        # Perfil de Windows PowerShell y, si lo tienes, el de PowerShell 7 (pwsh)
        $Perfiles = @($PROFILE.CurrentUserAllHosts)
        if (Tiene pwsh) { $Perfiles += (pwsh -NoProfile -Command '$PROFILE.CurrentUserAllHosts') }
        foreach ($Perfil in ($Perfiles | Select-Object -Unique)) {
            if (-not (Test-Path $Perfil)) { New-Item -ItemType File -Force $Perfil | Out-Null }
            if (-not (Select-String -Path $Perfil -SimpleMatch $ScriptTab -Quiet)) {
                Add-Content -Path $Perfil -Value "`r`n$Linea" -Encoding UTF8
            }
            Ok "TAB activado en $Perfil"
        }
        Ok "En una terminal nueva prueba: dam ej<TAB>"
    }
}

# 5. git: identidad --------------------------------------------------------
# (Las credenciales las guarda el «Git Credential Manager» que trae Git para Windows.)
Paso "Preparo git para los commits de dam sync"
if (-not (git config --global user.name)) {
    $nombre = Read-Host "    Tu nombre para los commits"
    if ($nombre) { git config --global user.name "$nombre" }
}
if (-not (git config --global user.email)) {
    $correo = Read-Host "    Tu correo de GitHub"
    if ($correo) { git config --global user.email "$correo" }
}
$nombre = git config --global user.name
$correo = git config --global user.email
if ($nombre -and $correo) {
    Ok "git firmará como: $nombre <$correo>"
} else {
    Aviso "Sin nombre o correo, git no podrá hacer commits. Vuelve a ejecutar este script."
}

# 6. Almacén de apuntes ----------------------------------------------------
Paso "Almacén de apuntes"
$Almacen = $env:DAM_ALMACEN
if (-not $Almacen) { $Almacen = [Environment]::GetEnvironmentVariable('DAM_ALMACEN', 'User') }
if (-not $Almacen) {
    # ¿Ya está clonado en otro sitio (por ejemplo en Documentos)? Se busca hasta 3 niveles dentro de
    # tu carpeta personal un repo git cuyo remoto sea DAM-almacen, se llame como se llame la carpeta.
    # No entra en carpetas ocultas, AppData, node_modules, enlaces ni dentro de otros repos.
    function Buscar-Almacen($carpeta, $nivel) {
        Get-ChildItem -LiteralPath $carpeta -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '^\.' -and $_.Name -notin 'AppData', 'node_modules' -and
                           -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
            ForEach-Object {
                if (Test-Path (Join-Path $_.FullName '.git')) {
                    $remoto = git -C $_.FullName remote get-url origin 2>$null
                    if ($remoto -match '/dam-almacen') { $_.FullName }
                } elseif ($nivel -lt 3) {
                    Buscar-Almacen $_.FullName ($nivel + 1)
                }
            }
    }
    $Encontrados = @(Buscar-Almacen $HOME 1 | Sort-Object)
    if ($Encontrados.Count -gt 0) {
        $Almacen = $Encontrados[0]
        if ($Encontrados.Count -gt 1) {
            Aviso "Hay $($Encontrados.Count) copias del almacén: $($Encontrados -join ', ')"
            Aviso "Uso la primera. Para usar otra, cambia la variable DAM_ALMACEN de tu usuario."
        }
        if ($Almacen -ne (Join-Path $HOME "DAM-almacen")) {
            # dam lo busca en ~/DAM-almacen (acciones.json): si está en otro sitio, se lo digo con
            # DAM_ALMACEN como variable de tu usuario (la ven PowerShell, cmd y Git Bash)
            [Environment]::SetEnvironmentVariable('DAM_ALMACEN', $Almacen, 'User')
            Ok "Guardado DAM_ALMACEN=$Almacen en las variables de tu usuario"
        }
    } else {
        $Almacen = Join-Path $HOME "DAM-almacen"
    }
}
$env:DAM_ALMACEN = $Almacen
if (Test-Path (Join-Path $Almacen ".git")) {
    Ok "Ya está clonado en $Almacen"
} elseif (Test-Path $Almacen) {
    Aviso "$Almacen existe pero no es un repositorio git: no lo toco."
} else {
    $usuario = Read-Host "    Tu usuario de GitHub para clonar DAM-almacen (Enter para saltar)"
    if ($usuario) {
        git clone "https://github.com/$usuario/DAM-almacen.git" "$Almacen"
        if ($LASTEXITCODE -eq 0) {
            Ok "Clonado en $Almacen"
        } else {
            Aviso "No he podido clonarlo: revisa el usuario, el inicio de sesión y que el repo se llame DAM-almacen."
        }
    } else {
        Aviso "Saltado. Luego: git clone https://github.com/TU_USUARIO/DAM-almacen.git $Almacen"
    }
}

# 7. Comprobación final ----------------------------------------------------
Paso "Compruebo que todo funciona"
uv run dam --config "$Config" validar

Write-Host ""
Write-Host "Listo. Prueba:  dam --help   y   dam status"
