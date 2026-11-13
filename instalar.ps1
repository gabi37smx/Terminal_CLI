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

# 4. Dónde van tus acciones (las configura el paso 6b, con el almacén ya clonado)
$Config = Join-Path $HOME ".config\dam\acciones.json"

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
# Solo se busca si ya lo tienes. Si no, se baja o se crea en el paso 6b, después de elegir el ciclo:
# se llama como tu ciclo (DAM-almacen, ASIR-almacen...) y dam te ayuda a crearlo (ADR-0005).
Paso "Almacén de apuntes"
$Almacen = $env:DAM_ALMACEN
if (-not $Almacen) { $Almacen = [Environment]::GetEnvironmentVariable('DAM_ALMACEN', 'User') }
if ($Almacen) {
    $env:DAM_ALMACEN = $Almacen
    Ok "Uso el de DAM_ALMACEN: $Almacen"
} else {
    # ¿Ya está clonado (por ejemplo en Documentos)? Se busca hasta 3 niveles dentro de tu carpeta
    # personal un repo git cuyo remoto sea CICLO-almacen, se llame como se llame la carpeta.
    # No entra en carpetas ocultas, AppData, node_modules, enlaces ni dentro de otros repos.
    function Buscar-Almacen($carpeta, $nivel) {
        Get-ChildItem -LiteralPath $carpeta -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '^\.' -and $_.Name -notin 'AppData', 'node_modules' -and
                           -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
            ForEach-Object {
                if (Test-Path (Join-Path $_.FullName '.git')) {
                    $remoto = git -C $_.FullName remote get-url origin 2>$null
                    if ($remoto -match '/(smx|dam|daw|asir|apuntes)-almacen(\.git)?/?$') { $_.FullName }
                } elseif ($nivel -lt 3) {
                    Buscar-Almacen $_.FullName ($nivel + 1)
                }
            }
    }
    $Encontrados = @(Buscar-Almacen $HOME 1 | Sort-Object)
    if ($Encontrados.Count -gt 0) {
        $Almacen = $Encontrados[0]
        Ok "Ya lo tienes en $Almacen"
        if ($Encontrados.Count -gt 1) {
            Aviso "Hay $($Encontrados.Count) copias del almacén: $($Encontrados -join ', ')"
            Aviso "Uso la primera. Para usar otra, cambia la variable DAM_ALMACEN de tu usuario."
        }
        $EnSuSitio = 'SMX', 'DAM', 'DAW', 'ASIR', 'APUNTES' | ForEach-Object { Join-Path $HOME "$_-almacen" }
        if ($Almacen -notin $EnSuSitio) {
            # dam lo busca en ~/CICLO-almacen (acciones.json): si está en otro sitio, se lo digo con
            # DAM_ALMACEN como variable de tu usuario (la ven PowerShell, cmd y Git Bash)
            [Environment]::SetEnvironmentVariable('DAM_ALMACEN', $Almacen, 'User')
            Ok "Guardado DAM_ALMACEN=$Almacen en las variables de tu usuario"
        }
        $env:DAM_ALMACEN = $Almacen
    } else {
        Write-Host "    Aún no lo tienes en este equipo: después de elegir tu ciclo te ayudo a bajarlo o a crearlo."
    }
}

# 6b. Tu ciclo, tus asignaturas y tu almacén ---------------------------------
# Como adduser en Linux: pregunta qué estudias y deja acciones.json a tu medida. Al acabar ofrece
# preparar el almacén (se llama como tu ciclo). Si no se configura, se prepara igual con crear-almacen.
Paso "Tu ciclo y tus asignaturas (dam configurar)"
# Sin función: en PowerShell lo que escribe una función es su resultado y no se verían las preguntas
$Configurado = $false
if (-not (Test-Path $Config)) {
    uv run dam --config "$Config" configurar --plantilla acciones.json
    if ($LASTEXITCODE -eq 0) {
        $Configurado = $true
    } else {
        New-Item -ItemType Directory -Force (Split-Path $Config) | Out-Null
        Copy-Item acciones.json $Config
        Aviso "No se ha configurado: he copiado las acciones de 1º de DAM a $Config."
        Aviso "Cuando quieras, elige tu ciclo con:  dam configurar"
    }
} elseif ((Get-FileHash acciones.json).Hash -eq (Get-FileHash $Config).Hash) {
    Ok "Ya tienes $Config y está al día (para cambiar de ciclo o de curso: dam configurar)"
} else {
    # O ya elegiste tus asignaturas o es de una instalación vieja (le faltarían las acciones nuevas)
    Aviso "Tu $Config no es igual que la del repo: ya elegiste tus asignaturas o es de una instalación vieja."
    $respuesta = Read-Host "    ¿La rehago con las acciones del repo? Te propongo lo que elegiste y guardo una copia [s/N]"
    if ($respuesta -eq 's') {
        uv run dam --config "$Config" configurar --plantilla acciones.json
        if ($LASTEXITCODE -eq 0) { $Configurado = $true } else { Aviso "No he cambiado nada: dam seguirá usando la tuya." }
    } else {
        Aviso "No la toco: dam seguirá usando la tuya."
    }
}
if (-not $Configurado) {
    Paso "Tu almacén de apuntes (dam crear-almacen)"
    uv run dam --config "$Config" crear-almacen
    if ($LASTEXITCODE -ne 0) { Aviso "Sin almacén de momento. Cuando quieras:  dam crear-almacen" }
}

# 6c. IA para las acciones que la usan --------------------------------------
# Modelos gratis con OpenCode: funcionan en casa y no piden clave (ADR-0004). Se instala la misma
# versión de OpenCode que usamos en clase: con ella está probado el agente de dam.
Paso "IA para las acciones que la usan (dam configurar-ia)"
$VersionOpenCode = "1.18.35"
if (Test-Path (Join-Path $HOME ".config\dam\ia.json")) {
    Ok "Ya elegiste el modelo (para cambiarlo: dam configurar-ia)"
} else {
    if (-not (Tiene opencode)) {
        $respuesta = Read-Host "    Para usar modelos de IA gratis hace falta OpenCode. ¿Lo instalo? [S/n]"
        if ($respuesta -ne 'n') {
            if (Tiene npm) {
                npm install -g "opencode-ai@$VersionOpenCode"
                if ($LASTEXITCODE -ne 0) { Aviso "npm no ha podido instalar OpenCode." }
                $env:Path = "$env:APPDATA\npm;$env:Path"   # ahí deja npm sus comandos: que esta ventana lo vea ya
            } else {
                Aviso "Para instalar OpenCode necesito npm (Node.js): winget install OpenJS.NodeJS.LTS"
                Aviso "Después, cierra esta ventana y repite el instalador: lo que ya está hecho se salta."
            }
        }
    }
    if (Tiene opencode) {
        # Sin función: así se ven las preguntas (como en el paso 6b)
        uv run dam configurar-ia
        if ($LASTEXITCODE -ne 0) { Aviso "Sin IA de momento. Cuando quieras: dam configurar-ia" }
    } else {
        Aviso "Sin OpenCode, las acciones con IA usan el servidor del centro (o elige con: dam configurar-ia)."
    }
}

# 7. Comprobación final ----------------------------------------------------
Paso "Compruebo que todo funciona"
uv run dam --config "$Config" validar

Write-Host ""
Write-Host "Listo. Prueba:  dam --help   y   dam status"
