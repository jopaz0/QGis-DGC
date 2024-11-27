"""
Modulo: AyudasGEO (25 Nov 2024)

Tipee help(funcion) en la consola para mas informacion.
#################BARRA SEPARADORA DE BAJO PRESUPUESTO#################
"""
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from CommonFunctions import *
from DGCFunctions import *

def CargarWFS(ejido, todo=False):
    try:
        ejidos = LeerDicEjidos()
        info = ejidos[ejido]
        if todo:
            pass
        else:
            name = f"{STR_FillWithChars(ejido,3)}-{info['NOMBRE']}-Propietarios-IDE"
            typename = f"p_dirg_catastro:{info['NOMBREIDE']}_pu"
            layer = CANVAS_AddLayerFromWFS(name, typename)
            return layer
    except Exception as e:
        print(f"ERROR: {e}")
        return None
cargarwfs = CargarWFS