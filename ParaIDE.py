import tempfile
import sys
import os
import datetime
import urllib.request
import importlib.util

tempFolder = tempfile.gettempdir()
sys.path.append(tempFolder)
depNames = ['CommonFunctions', 'DGCFunctions', 'ChamferTool', 'NumberingTool']
DGCModuleNames = ['Digitalizacion']
for name in depNames + DGCModuleNames:
    filePath = os.path.join(tempFolder, f"{name}.py")
    if os.path.exists(filePath):
        os.remove(filePath)
    url = f'https://raw.githubusercontent.com/jopaz0/QGis-DGC/refs/heads/main/{name}.py'
    try:
        urllib.request.urlretrieve(url, filePath)
        spec = importlib.util.spec_from_file_location(name, filePath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for func_name in dir(module):
            if callable(getattr(module, func_name)) and not func_name.startswith("__"):
                globals()[func_name] = getattr(module, func_name)
        if name in DGCModuleNames:
            print(module.__doc__)
    except Exception as e:
        print(f"Error al descargar o importar {name}: {e}")