"""Vocabulario de los ciclos de Informática: qué asignaturas tiene cada curso y cómo reconocer sus ficheros.

Lo usa «dam configurar» para preguntar qué estudias y rellenar acciones.json con TUS asignaturas
(las carpetas y palabras clave de «ordenar» y las categorías de «clasificar»).

- Cada asignatura tiene un nombre corto (el de la carpeta), su nombre en castellano y en valenciano,
  palabras clave (en los dos idiomas, sin tildes: dam las quita al comparar) y, si las hay,
  extensiones que solo usa esa asignatura.
- Los módulos comunes (inglés, itinerario para la empleabilidad, proyecto intermodular...) son la
  misma carpeta en todos los ciclos.
- Plan de estudios nuevo (LOFP). Dónde cae cada módulo común puede cambiar según el centro:
  por eso «dam configurar» deja quitar y añadir asignaturas.

Para añadir un ciclo: sus asignaturas en ASIGNATURAS y el ciclo en CICLOS. No hay que tocar nada más.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Asignatura:
    castellano: str
    valenciano: str
    palabras: tuple[str, ...]
    extensiones: tuple[str, ...] = field(default=())


A = Asignatura  # para que la tabla de abajo se lea mejor

ASIGNATURAS: dict[str, Asignatura] = {
    # --- Comunes a todos los ciclos ---
    "ingles": A("Inglés profesional", "Anglés professional", ("english", "ingles", "vocabulary", "grammar")),
    "ipo": A("Itinerario personal para la empleabilidad", "Itinerari personal per a l'ocupabilitat",
             ("ipo", "empleabilidad", "curriculum", "entrevista")),
    "proyecto": A("Proyecto intermodular", "Projecte intermodular",
                  ("projecte", "proyecto", "intermodular", "multiplataforma")),
    "digitalizacion": A("Digitalización aplicada a los sectores productivos",
                        "Digitalització aplicada als sectors productius",
                        ("digitalizacion", "digitalitzacio", "industria 4 0", "transformacion digital",
                         "transformacio digital")),
    "sostenibilidad": A("Sostenibilidad aplicada al sistema productivo",
                        "Sostenibilitat aplicada al sistema productiu",
                        ("sostenibilidad", "sostenibilitat", "ods", "medio ambiente", "medi ambient",
                         "huella de carbono", "petjada de carboni")),

    # --- 1º de DAM y DAW (las palabras son las del acciones.json del repo: no cambiarlas sin él) ---
    "bases-datos": A("Bases de datos", "Bases de dades",
                     ("base de dades", "bases de dades", "bases de datos", "sql", "mysql", "consulta",
                      "taula", "tabla"),
                     (".sql", ".db")),
    "entornos": A("Entornos de desarrollo", "Entorns de desenvolupament",
                  ("entorns", "entornos", "git", "ide", "compilador", "docker")),
    "lenguaje-marcas": A("Lenguajes de marcas y sistemas de gestión de información",
                         "Llenguatges de marques i sistemes de gestió d'informació",
                         ("llenguatge de marques", "lenguaje de marcas", "marques", "marcas", "xml", "html",
                          "json"),
                         (".xml", ".html", ".htm")),
    "programacion": A("Programación", "Programació",
                      ("programacio ia", "programacio", "programacion", "python", "poo", "classe", "clase",
                       "funcio", "funcion", "objecte", "objeto"),
                      (".py", ".java")),
    "sistemas": A("Sistemas informáticos", "Sistemes informàtics",
                  ("sistemes", "sistemas", "linux", "xarxes", "redes", "hardware", "so", "sistemes informatics",
                   "sistemas informaticos", "arquitectura", "von neumann", "ordinador", "ordinadors",
                   "ordenador", "ordenadores", "computadora", "cpu", "ucp", "processador", "procesador",
                   "maquinari", "xarxa", "windows"),
                  (".sh",)),

    # --- 2º de DAM ---
    "acceso-datos": A("Acceso a datos", "Accés a dades",
                      ("acceso a datos", "acces a dades", "jdbc", "orm", "hibernate", "mongodb", "persistencia",
                       "ficheros", "fitxers")),
    "interfaces": A("Desarrollo de interfaces", "Desenvolupament d'interfícies",
                    ("interfaces", "interficies", "javafx", "swing", "usabilidad", "usabilitat", "informes",
                     "componentes", "components")),
    "moviles": A("Programación multimedia y dispositivos móviles",
                 "Programació multimèdia i dispositius mòbils",
                 ("android", "kotlin", "movil", "moviles", "mobil", "mobils", "multimedia", "unity",
                  "videojuego", "videojoc"),
                 (".kt",)),
    "servicios-procesos": A("Programación de servicios y procesos", "Programació de serveis i processos",
                            ("procesos", "processos", "hilos", "fils", "threads", "sockets", "concurrencia",
                             "servicios y procesos", "serveis i processos")),
    "gestion-empresarial": A("Sistemas de gestión empresarial", "Sistemes de gestió empresarial",
                             ("odoo", "erp", "crm", "gestion empresarial", "gestio empresarial")),

    # --- 2º de DAW ---
    "cliente": A("Desarrollo web en entorno cliente", "Desenvolupament web en entorn client",
                 ("cliente", "client", "javascript", "dom", "typescript", "react", "fetch", "eventos", "esdeveniments"),
                 (".js", ".ts")),
    "servidor": A("Desarrollo web en entorno servidor", "Desenvolupament web en entorn servidor",
                  ("servidor", "php", "laravel", "node", "express", "api", "sesiones", "sessions"),
                  (".php",)),
    "despliegue": A("Despliegue de aplicaciones web", "Desplegament d'aplicacions web",
                    ("despliegue", "desplegament", "apache", "nginx", "tomcat", "dns", "https", "certificado",
                     "certificat")),
    "diseno-interfaces": A("Diseño de interfaces web", "Disseny d'interfícies web",
                           ("diseno", "disseny", "css", "sass", "figma", "accesibilidad", "accessibilitat",
                            "responsive", "maquetacion", "maquetacio"),
                           (".css", ".scss")),

    # --- 1º de ASIR ---
    "sistemas-operativos": A("Implantación de sistemas operativos", "Implantació de sistemes operatius",
                             ("sistemas operativos", "sistemes operatius", "so", "linux", "windows", "ubuntu",
                              "particiones", "particions", "usuarios", "usuaris", "virtualbox", "instalacion",
                              "installacio"),
                             (".sh", ".ps1", ".bat")),
    "redes": A("Planificación y administración de redes", "Planificació i administració de xarxes",
               ("redes", "xarxes", "xarxa", "red", "router", "switch", "vlan", "tcp", "subred", "subxarxa",
                "cisco", "packet tracer", "enrutamiento", "encaminament"),
               (".pkt", ".pcap", ".pcapng")),
    "hardware": A("Fundamentos de hardware", "Fonaments de maquinari",
                  ("hardware", "maquinari", "cpu", "placa base", "memoria", "disco", "disc", "fuente", "font",
                   "bios", "uefi", "componentes", "components")),

    # --- 2º de ASIR (servicios-red, aplicaciones-web y seguridad también son de 2º de SMX) ---
    "admin-sistemas": A("Administración de sistemas operativos", "Administració de sistemes operatius",
                        ("administracion", "administracio", "active directory", "ldap", "dominio", "domini",
                         "scripts", "powershell", "bash", "servicios", "serveis"),
                        (".sh", ".ps1", ".bat")),
    "servicios-red": A("Servicios de red e Internet (en SMX: Servicios en red)",
                       "Serveis de xarxa i Internet (en SMX: Serveis en xarxa)",
                       ("servicios de red", "serveis de xarxa", "servicios en red", "serveis en xarxa", "dhcp",
                        "dns", "ftp", "ssh", "correo", "correu", "proxy", "servidor web")),
    "aplicaciones-web": A("Implantación de aplicaciones web (en SMX: Aplicaciones web)",
                          "Implantació d'aplicacions web (en SMX: Aplicacions web)",
                          ("aplicaciones web", "aplicacions web", "cms", "wordpress", "moodle", "php", "lamp",
                           "xampp", "blog"),
                          (".php",)),
    "admin-bases-datos": A("Administración de sistemas gestores de bases de datos",
                           "Administració de sistemes gestors de bases de dades",
                           ("sgbd", "sistemas gestores", "sistemes gestors", "copias de seguridad",
                            "copies de seguretat", "usuarios y permisos", "replicacion", "replicacio", "sql",
                            "mysql", "oracle", "postgresql"),
                           (".sql",)),
    "seguridad": A("Seguridad y alta disponibilidad (en SMX: Seguridad informática)",
                   "Seguretat i alta disponibilitat (en SMX: Seguretat informàtica)",
                   ("seguridad", "seguretat", "cortafuegos", "tallafocs", "firewall", "vpn", "cifrado", "xifratge",
                    "copias de seguridad", "copies de seguretat", "alta disponibilidad", "alta disponibilitat",
                    "malware", "antivirus")),

    # --- 1º de SMX ---
    "montaje-equipos": A("Montaje y mantenimiento de equipos", "Muntatge i manteniment d'equips",
                         ("montaje", "muntatge", "mantenimiento", "manteniment", "hardware", "maquinari",
                          "placa base", "cpu", "memoria", "fuente", "font", "bios", "uefi", "componentes",
                          "components")),
    "sistemas-monopuesto": A("Sistemas operativos monopuesto", "Sistemes operatius monolloc",
                             ("monopuesto", "monolloc", "sistemas operativos", "sistemes operatius", "so",
                              "windows", "linux", "ubuntu", "particiones", "particions", "virtualbox"),
                             (".sh", ".bat", ".ps1")),
    "ofimatica": A("Aplicaciones ofimáticas", "Aplicacions ofimàtiques",
                   ("ofimatica", "ofimatiques", "word", "excel", "writer", "calc", "powerpoint", "impress",
                    "hoja de calculo", "full de calcul", "procesador de textos", "processador de textos")),
    "redes-locales": A("Redes locales", "Xarxes locals",
                       ("redes locales", "xarxes locals", "redes", "xarxes", "xarxa", "red", "cableado",
                        "cablejat", "switch", "router", "rj45", "tcp", "packet tracer", "cisco"),
                       (".pkt", ".pcap", ".pcapng")),

    # --- 2º de SMX ---
    "sistemas-red": A("Sistemas operativos en red", "Sistemes operatius en xarxa",
                      ("sistemas operativos en red", "sistemes operatius en xarxa", "dominio", "domini",
                       "active directory", "ldap", "samba", "windows server", "usuarios", "usuaris"),
                      (".sh", ".bat", ".ps1")),
}

DAM_DAW_1 = ["bases-datos", "entornos", "ingles", "ipo", "lenguaje-marcas", "programacion", "proyecto", "sistemas"]
COMUNES_2 = ["ipo", "proyecto", "digitalizacion", "sostenibilidad"]


@dataclass(frozen=True)
class Ciclo:
    nombre: str  # el que se enseña («1º de DAM»)
    titulo: str
    cursos: dict[int, list[str]]  # curso -> asignaturas, en orden alfabético (en un empate gana la primera)


CICLOS: dict[str, Ciclo] = {
    "smx": Ciclo("SMX", "Sistemas Microinformáticos y Redes (grado medio)", {
        1: ["ingles", "ipo", "montaje-equipos", "ofimatica", "proyecto", "redes-locales", "sistemas-monopuesto"],
        2: ["aplicaciones-web", "seguridad", "servicios-red", "sistemas-red", *COMUNES_2],
    }),
    "dam": Ciclo("DAM", "Desarrollo de Aplicaciones Multiplataforma", {
        1: DAM_DAW_1,
        2: ["acceso-datos", "gestion-empresarial", "interfaces", "moviles", "servicios-procesos", *COMUNES_2],
    }),
    "daw": Ciclo("DAW", "Desarrollo de Aplicaciones Web", {
        1: DAM_DAW_1,
        2: ["cliente", "despliegue", "diseno-interfaces", "servidor", *COMUNES_2],
    }),
    "asir": Ciclo("ASIR", "Administración de Sistemas Informáticos en Red (ASIX en valenciano)", {
        1: ["bases-datos", "hardware", "ingles", "ipo", "lenguaje-marcas", "proyecto", "redes", "sistemas-operativos"],
        2: ["admin-bases-datos", "admin-sistemas", "aplicaciones-web", "seguridad", "servicios-red", *COMUNES_2],
    }),
}
OTRO = "otro"  # ningún ciclo de la lista: empiezas sin asignaturas y las escribes tú
ALIAS = {"asix": "asir"}  # el nombre en valenciano (y en catalán)


def ciclo_valido(texto: str) -> str:
    """'ASIX' -> 'asir'. Lanza ValueError si no es ninguno."""
    clave = ALIAS.get(texto.strip().lower(), texto.strip().lower())
    if clave not in CICLOS and clave != OTRO:
        opciones = ", ".join([*CICLOS, *ALIAS, OTRO])
        raise ValueError(f"«{texto}» no es un ciclo que conozca; usa uno de: {opciones}")
    return clave


def asignaturas_de(ciclo: str, cursos: list[int]) -> dict[str, list[str]]:
    """Las asignaturas de esos cursos con sus palabras clave: {"redes": ["redes", "xarxes", ...]}.

    Con los dos cursos van primero las de 1º (en un empate de palabras gana la primera).
    """
    if ciclo == OTRO:
        return {}
    datos = CICLOS[ciclo]
    resultado: dict[str, list[str]] = {}
    for curso in sorted(set(cursos)):
        if curso not in datos.cursos:
            raise ValueError(f"{datos.nombre} no tiene {curso}º curso; usa 1 o 2")
        for nombre in datos.cursos[curso]:
            resultado.setdefault(nombre, list(ASIGNATURAS[nombre].palabras))
    return resultado


def por_extension(asignaturas: list[str]) -> dict[str, str]:
    """{".py": "programacion", ...} para esas asignaturas. Si dos usan la misma extensión, la primera."""
    resultado: dict[str, str] = {}
    for nombre in asignaturas:
        for ext in ASIGNATURAS[nombre].extensiones if nombre in ASIGNATURAS else ():
            resultado.setdefault(ext, nombre)
    return resultado


def nombre_largo(asignatura: str) -> str:
    """'redes' -> 'Planificación y administración de redes / Planificació i administració de xarxes'."""
    a = ASIGNATURAS.get(asignatura)
    return f"{a.castellano} / {a.valenciano}" if a else asignatura


def etiqueta(ciclo: str, cursos: list[int]) -> str:
    """'dam', [1] -> '1º de DAM'; 'smx', [1, 2] -> 'SMX'; 'otro' -> 'tu curso'."""
    if ciclo == OTRO:
        return "tu curso"
    nombre = CICLOS[ciclo].nombre
    return f"{cursos[0]}º de {nombre}" if len(set(cursos)) == 1 else nombre


def a_nombre_de_carpeta(texto: str) -> str:
    """'Formación y Orientación Laboral' -> 'formacion-y-orientacion-laboral' (minúsculas, sin tildes, guiones)."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "-".join(re.findall(r"[a-z0-9]+", sin_tildes.lower()))
