"""
DGC Python Functions (09 Oct 2024)
Created for use at DGC with PyQGis, only work in that enviroment due to file structure. Docstrings and variable names are in spanish, as a deference for coworkers that may have to update this someday.

"""
import os
from CommonFunctions import *

def BuscarCapasUrbanas(numeroDeEjido):
    """
    Busca y devuelve las rutas de las capas urbanas (PROPIETARIOS y POSEEDORES) en el sistema de archivos. A futuro incluira el resto de capas del pueblo

    PARAMETROS
    ejido: String que representa el nombre del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.

    COMENTARIOS
    - La función asume que las capas están organizadas en carpetas específicas dentro de una carpeta raíz.
    - Se construyen las rutas a las capas de propietarios y poseedores a partir de la estructura de carpetas.

    RETURNOS
    Un diccionario con las rutas de las capas urbanas, donde las claves son 'PROPIETARIOS' y 'POSEEDORES'.
    """

    directorioPueblosCADGIS = r'L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    numeroDeEjido = STR_FillWithChars(numeroDeEjido, 3, '0')
    capas = {}
    carpetaEjido = [os.path.join(directorioPueblosCADGIS, d) for d in os.listdir(directorioPueblosCADGIS) if os.path.isdir(os.path.join(directorioPueblosCADGIS, d)) and d.startswith(numeroDeEjido)][0]
    carpetaPoligonos = [os.path.join(carpetaEjido, d) for d in os.listdir(carpetaEjido) if os.path.isdir(os.path.join(carpetaEjido, d)) and 'POLIGONO' in d.upper()][0]

    capas['PROPIETARIOS'] = [os.path.join(carpetaPoligonos, d) for d in os.listdir(carpetaPoligonos) if os.path.isfile(os.path.join(carpetaPoligonos, d)) and 'PROPIETARIO' in d.upper() and d.lower().endswith('.shp')][0]
    capas['POSEEDORES'] = [os.path.join(carpetaPoligonos, d) for d in os.listdir(carpetaPoligonos) if os.path.isfile(os.path.join(carpetaPoligonos, d)) and 'POSEEDOR' in d.upper() and d.lower().endswith('.shp')][0]
    return capas
