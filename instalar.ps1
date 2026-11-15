# Instala y configura mochila en Windows.
# Uso: doble clic en instalar.cmd, o desde PowerShell:
#   powershell -ExecutionPolicy Bypass -File instalar.ps1
# Se puede ejecutar todas las veces que quieras: lo que ya está hecho se salta.
# (Guardado en UTF-8 con BOM para que Windows PowerShell 5 lea bien las tildes.)

$ErrorActionPreference = 'Continue'   # los fallos de git/uv se comprueban con $LASTEXITCODE
Set-Location $PSScriptRoot            # trabaja siempre desde la carpeta del repositorio
$PathOriginal = $env:Path             # para saber después si tu terminal ya encuentra «mochila»

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

# 3. Dependencias y comando mochila --------------------------------------------
Paso "Instalo las dependencias (uv descarga Python 3.12 si hace falta)"
uv sync
if ($LASTEXITCODE -ne 0) { Parar "uv sync ha fallado (mira el mensaje de arriba)." }

Paso "Instalo el comando mochila para todo el sistema"
uv tool install --editable . --force
if ($LASTEXITCODE -ne 0) { Parar "No he podido instalar el comando mochila." }
$CarpetaBin = (uv tool dir --bin).Trim()
if (($PathOriginal -split ';') -contains $CarpetaBin) {
    Ok "Tu terminal ya encuentra los comandos de $CarpetaBin"
} else {
    uv tool update-shell
    Aviso "Al terminar, cierra esta terminal y abre otra para que «mochila» funcione."
}

# 4. Dónde van tus acciones (las configura el paso 6b, con el almacén ya clonado)
$Config = Join-Path $HOME ".config\mochila\acciones.json"

# Antes se llamaba «dam»: lo que ya elegiste (acciones.json, ia.json) se copia a .config\mochila.
# La carpeta vieja se queda como copia de seguridad; puedes borrarla cuando quieras.
$ConfigVieja = Join-Path $HOME ".config\dam"
if ((Test-Path $ConfigVieja) -and -not (Test-Path (Split-Path $Config))) {
    Copy-Item -Recurse $ConfigVieja (Split-Path $Config)
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path (Split-Path $Config) "completado.ps1")
    Ok "Lo que tenías de dam pasa a $(Split-Path $Config)"
}
$AlmacenViejo = [Environment]::GetEnvironmentVariable('DAM_ALMACEN', 'User')
if ($AlmacenViejo -and -not [Environment]::GetEnvironmentVariable('MOCHILA_ALMACEN', 'User')) {
    [Environment]::SetEnvironmentVariable('MOCHILA_ALMACEN', $AlmacenViejo, 'User')
    [Environment]::SetEnvironmentVariable('DAM_ALMACEN', $null, 'User')
    $env:MOCHILA_ALMACEN = $AlmacenViejo
    Ok "La variable DAM_ALMACEN pasa a llamarse MOCHILA_ALMACEN"
}

# 4b. Autocompletado con TAB -----------------------------------------------
# No uso «mochila --install-completion»: cambiaría la política de PowerShell a Unrestricted
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
    $ScriptTab = Join-Path $HOME ".config\mochila\completado.ps1"
    # En un Windows recién instalado aún no existe .config\mochila (acciones.json se crea en el paso 6b)
    New-Item -ItemType Directory -Force (Split-Path $ScriptTab) | Out-Null
    # Con esta variable, mochila no ejecuta nada: solo escribe el script de autocompletado
    $env:_MOCHILA_COMPLETE = "source_powershell"
    $Texto = & (Join-Path $CarpetaBin "mochila.exe")
    Remove-Item Env:_MOCHILA_COMPLETE
    if ($LASTEXITCODE -eq 0 -and $Texto) {
        Set-Content -Path $ScriptTab -Value ($Texto -join "`r`n") -Encoding UTF8
    }
    if (-not (Test-Path $ScriptTab)) {
        # Sin el script no toco el perfil: cada PowerShell nueva daría un error en rojo
        Aviso "No he podido generar el autocompletado."
    } else {
        $Linea = ". `"$ScriptTab`"  # autocompletado de mochila (lo añadió instalar.ps1)"
        # Perfil de Windows PowerShell y, si lo tienes, el de PowerShell 7 (pwsh)
        $Perfiles = @($PROFILE.CurrentUserAllHosts)
        if (Tiene pwsh) { $Perfiles += (pwsh -NoProfile -Command '$PROFILE.CurrentUserAllHosts') }
        foreach ($Perfil in ($Perfiles | Select-Object -Unique)) {
            if (-not (Test-Path $Perfil)) { New-Item -ItemType File -Force $Perfil | Out-Null }
            # La línea de cuando se llamaba dam carga un script que ya no se usa: fuera
            $Lineas = @(Get-Content -Path $Perfil -Encoding UTF8)
            $SinVieja = @($Lineas | Where-Object { $_ -notmatch 'autocompletado de dam \(lo añadió instalar\.ps1\)' })
            if ($SinVieja.Count -ne $Lineas.Count) { Set-Content -Path $Perfil -Value $SinVieja -Encoding UTF8 }
            if (-not (Select-String -Path $Perfil -SimpleMatch $ScriptTab -Quiet)) {
                Add-Content -Path $Perfil -Value "`r`n$Linea" -Encoding UTF8
            }
            Ok "TAB activado en $Perfil"
        }
        Ok "En una terminal nueva prueba: mochila ej<TAB>"
    }
}

# 5. git: identidad --------------------------------------------------------
# (Las credenciales las guarda el «Git Credential Manager» que trae Git para Windows.)
Paso "Preparo git para los commits de mochila sync"
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
# se llama como tu ciclo (DAM-almacen, ASIR-almacen...) y mochila te ayuda a crearlo (ADR-0005).
Paso "Almacén de apuntes"
$Almacen = $env:MOCHILA_ALMACEN
if (-not $Almacen) { $Almacen = [Environment]::GetEnvironmentVariable('MOCHILA_ALMACEN', 'User') }
if ($Almacen) {
    $env:MOCHILA_ALMACEN = $Almacen
    Ok "Uso el de MOCHILA_ALMACEN: $Almacen"
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
            Aviso "Uso la primera. Para usar otra, cambia la variable MOCHILA_ALMACEN de tu usuario."
        }
        $EnSuSitio = 'SMX', 'DAM', 'DAW', 'ASIR', 'APUNTES' | ForEach-Object { Join-Path $HOME "$_-almacen" }
        if ($Almacen -notin $EnSuSitio) {
            # mochila lo busca en ~/CICLO-almacen (acciones.json): si está en otro sitio, se lo digo con
            # MOCHILA_ALMACEN como variable de tu usuario (la ven PowerShell, cmd y Git Bash)
            [Environment]::SetEnvironmentVariable('MOCHILA_ALMACEN', $Almacen, 'User')
            Ok "Guardado MOCHILA_ALMACEN=$Almacen en las variables de tu usuario"
        }
        $env:MOCHILA_ALMACEN = $Almacen
    } else {
        Write-Host "    Aún no lo tienes en este equipo: después de elegir tu ciclo te ayudo a bajarlo o a crearlo."
    }
}

# 6b. Tu ciclo, tus asignaturas y tu almacén ---------------------------------
# Como adduser en Linux: pregunta qué estudias y deja acciones.json a tu medida. Al acabar ofrece
# preparar el almacén (se llama como tu ciclo). Si no se configura, se prepara igual con crear-almacen.
Paso "Tu ciclo y tus asignaturas (mochila configurar)"
# Sin función: en PowerShell lo que escribe una función es su resultado y no se verían las preguntas
$Configurado = $false
if (-not (Test-Path $Config)) {
    uv run mochila --config "$Config" configurar --plantilla acciones.json
    if ($LASTEXITCODE -eq 0) {
        $Configurado = $true
    } else {
        New-Item -ItemType Directory -Force (Split-Path $Config) | Out-Null
        Copy-Item acciones.json $Config
        Aviso "No se ha configurado: he copiado las acciones de 1º de DAM a $Config."
        Aviso "Cuando quieras, elige tu ciclo con:  mochila configurar"
    }
} elseif ((Get-FileHash acciones.json).Hash -eq (Get-FileHash $Config).Hash) {
    Ok "Ya tienes $Config y está al día (para cambiar de ciclo o de curso: mochila configurar)"
} else {
    # O ya elegiste tus asignaturas o es de una instalación vieja (le faltarían las acciones nuevas)
    Aviso "Tu $Config no es igual que la del repo: ya elegiste tus asignaturas o es de una instalación vieja."
    $respuesta = Read-Host "    ¿La rehago con las acciones del repo? Te propongo lo que elegiste y guardo una copia [s/N]"
    if ($respuesta -eq 's') {
        uv run mochila --config "$Config" configurar --plantilla acciones.json
        if ($LASTEXITCODE -eq 0) { $Configurado = $true } else { Aviso "No he cambiado nada: mochila seguirá usando la tuya." }
    } else {
        Aviso "No la toco: mochila seguirá usando la tuya."
    }
}
if (-not $Configurado) {
    Paso "Tu almacén de apuntes (mochila crear-almacen)"
    uv run mochila --config "$Config" crear-almacen
    if ($LASTEXITCODE -ne 0) { Aviso "Sin almacén de momento. Cuando quieras:  mochila crear-almacen" }
}

# 6c. IA para las acciones que la usan --------------------------------------
# Modelos gratis con OpenCode: funcionan en casa y no piden clave (ADR-0004). Se instala la misma
# versión de OpenCode que usamos en clase: con ella está probado el agente de mochila.
Paso "IA para las acciones que la usan (mochila configurar-ia)"
$VersionOpenCode = "1.18.35"
if (Test-Path (Join-Path $HOME ".config\mochila\ia.json")) {
    Ok "Ya elegiste el modelo (para cambiarlo: mochila configurar-ia)"
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
        uv run mochila configurar-ia
        if ($LASTEXITCODE -ne 0) { Aviso "Sin IA de momento. Cuando quieras: mochila configurar-ia" }
    } else {
        Aviso "Sin OpenCode, las acciones con IA usan el servidor del centro (o elige con: mochila configurar-ia)."
    }
}

# 7. Comprobación final ----------------------------------------------------
Paso "Compruebo que todo funciona"
uv run mochila --config "$Config" validar

Write-Host ""
Write-Host "Listo. Prueba:  mochila --help   y   mochila status"
