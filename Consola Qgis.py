import sys
import os
import tempfile
import urllib.request
import importlib.util
import time
from collections import defaultdict
        
# === CONFIGURACIÓN GENERAL ===
LOCAL_REPO = r"L:\\Geodesia\\Privado\\Opazo\\QGis-DGC"
CACHE_MAX_AGE = 12 * 30 * 24 * 3600
GITHUB_USER = "jopaz0"
GITHUB_REPO = "QGis-DGC"
GITHUB_BRANCH = "main"

FUNCIONES = {}
tempFolder = tempfile.gettempdir()
sys.path.append(tempFolder)

# --- Módulos a cargar ---
depNames = ['CommonFunctions', 'DGCFunctions', 'ChamferTool', 'NumberingTool', 'DGCCustomExpressions']
DGCModuleNames = ['Digitalizacion', 'Sincronizacion', 'AyudasGEO']
allModules = depNames + DGCModuleNames

# --- Autenticación con token ---
headers = {
    "User-Agent": "QGIS-DGC-Loader",
    "Accept": "application/vnd.github.v3.raw"
}

with open(os.path.join(LOCAL_REPO, 'token.txt'), 'r', encoding='utf-8') as archivo:
  token = "github_pat_" + archivo.readline()

if token:
    headers["Authorization"] = f"Bearer {token}"

# === FUNCIONES AUXILIARES ===

def download_with_cache(name):
    """Descarga un módulo desde GitHub solo si no hay copia reciente en caché."""
    filePath = os.path.join(tempFolder, f"{name}.py")
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/{GITHUB_BRANCH}/{name}.py"

    if os.path.exists(filePath):
        age = time.time() - os.path.getmtime(filePath)
        if age < CACHE_MAX_AGE:
            print(f"Usando caché local para {name}.py")
            return filePath

    print(f"Descargando {name}.py desde GitHub...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response, open(filePath, "wb") as out_file:
            out_file.write(response.read())
        return filePath
    except Exception as e:
        raise RuntimeError(f"Error al descargar {name}: {e}")

def get_local_or_download(name):
    """Busca primero en la carpeta local compartida, luego descarga si es necesario."""
    local_path = os.path.join(LOCAL_REPO, f"{name}.py")
    if os.path.exists(local_path):
        print(f"Usando copia local para {name}.py")
        return local_path
    return download_with_cache(name)

def importar_modulo(name):
    """Importa dinámicamente un módulo desde su ruta local o descargada."""
    filePath = get_local_or_download(name)
    spec = importlib.util.spec_from_file_location(name, filePath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# === PROCESO PRINCIPAL ===

for name in allModules:
    try:
        module = importar_modulo(name)

        # Copiar funciones al espacio global
        for func_name in dir(module):
            func = getattr(module, func_name)
            if callable(func) and not func_name.startswith("__"):
                globals()[func_name] = func

        # Registrar FUNCIONES si existen
        if hasattr(module, "FUNCIONES"):
            for principal, info in module.FUNCIONES.items():
                FUNCIONES[principal] = {
                    "func": info["func"],
                    "aliases": info["aliases"],
                    "modulo": name
                }

    except Exception as e:
        print(f"Error al importar {name}: {e}")

# === RESUMEN DE FUNCIONES ===

agrupado = defaultdict(list)
for nombre, info in FUNCIONES.items():
    agrupado[info["modulo"]].append((nombre, info["aliases"]))

def ayuda():
    print("\nFunciones registradas:")
    for modulo in allModules:
        if modulo in agrupado:
            print(f"\n[{modulo}]")
            for principal, aliases in sorted(agrupado[modulo], key=lambda x: x[0].lower()):
                alias_txt = f" (aliases: {', '.join(aliases)})" if aliases else ""
                print(f"  - {principal}{alias_txt}")
    print("\nTipee 'help(\"funcion\")' para obtener más información.")
    print("Tipee 'ayuda()' para volver a mostrar este mensaje.")

aiuda = ayuda
aiuda()
