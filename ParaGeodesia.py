import sys
import os
import tempfile
import urllib.request
import importlib.util
from collections import defaultdict

# Registro global de todas las funciones recolectadas
FUNCIONES = {}

tempFolder = tempfile.gettempdir()
sys.path.append(tempFolder)

depNames = ['CommonFunctions', 'DGCFunctions', 'ChamferTool', 'NumberingTool', 'DGCCustomExpressions']
DGCModuleNames = ['Digitalizacion', 'Sincronizacion', 'AyudasGEO']
allModules = depNames + DGCModuleNames

for name in allModules:
    filePath = os.path.join(tempFolder, f"{name}.py")
    if os.path.exists(filePath):
        os.remove(filePath)
    url = f'https://raw.githubusercontent.com/jopaz0/QGis-DGC/refs/heads/main/{name}.py'

    try:
        # Descargar e importar
        urllib.request.urlretrieve(url, filePath)
        spec = importlib.util.spec_from_file_location(name, filePath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Copiar funciones al espacio global (para que se puedan usar directo)
        for func_name in dir(module):
            func = getattr(module, func_name)
            if callable(func) and not func_name.startswith("__"):
                globals()[func_name] = func

        # Recolectar el registro FUNCIONES del módulo si existe
        if hasattr(module, "FUNCIONES"):
            for principal, info in module.FUNCIONES.items():
                FUNCIONES[principal] = {
                    "func": info["func"],
                    "aliases": info["aliases"],
                    "modulo": name
                }

    except Exception as e:
        print(f"Error al descargar o importar {name}: {e}")

# --- Imprimir resumen agrupado por módulo ---
agrupado = defaultdict(list)
for nombre, info in FUNCIONES.items():
    agrupado[info["modulo"]].append((nombre, info["aliases"]))

print("\nFunciones registradas:")
for modulo in allModules:  # respeta el orden de carga
    if modulo in agrupado:
        print(f"\n[{modulo}]")
        for principal, aliases in sorted(agrupado[modulo], key=lambda x: x[0].lower()):
            alias_txt = f" (aliases: {', '.join(aliases)})" if aliases else ""
            print(f"  - {principal}{alias_txt}")
