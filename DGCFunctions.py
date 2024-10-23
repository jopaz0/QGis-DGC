"""
DGC Python Functions (09 Oct 2024)
Created for use at DGC with PyQGis, only work in that enviroment due to file structure. Docstrings and variable names are in spanish, as a deference for coworkers that may have to update this someday.

"""
import os
from CommonFunctions import *

def BuscarCapasUrbanas(numeroDeEjido):
    """
    Busca y devuelve las rutas de las capas urbanas en el sistema de archivos.

    PARAMETROS
    ejido: String 
        Representa el nombre del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.

    COMENTARIOS
    - La función asume que las capas están organizadas en carpetas específicas dentro de una carpeta raíz.
    - Se construyen las rutas a las capas de propietarios y poseedores a partir de la estructura de carpetas.

    RETORNOS
    Un diccionario con las rutas de las capas urbanas, donde las claves son PROPIETARIOS, POSEEDORES, EXPEDIENTES, MANZANAS, RADIOS, CIRCUNSCRIPCIONES, CALLES, MEDIDAS-REG, MEDIDAS-TITUOS y REGISTRADOS.
    """
    directorioPueblosCADGIS  = r'L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    if not os.path.exists(directorioPueblosCADGIS):
        directorioPueblosCADGIS  = r'C:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    numeroDeEjido = STR_FillWithChars(numeroDeEjido, 3, '0')
    capas = {}
    capas['PROPIETARIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'PROP'])
    capas['POSEEDORES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'POSE'])
    capas['EXPEDIENTES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'EXP', 'EXP'])
    capas['MANZANAS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'MANZ'])
    capas['RADIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'RAD'])
    capas['CIRCUNSCRIPCIONES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CIRC'])
    capas['CALLES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CALLE'])
    capas['MEDIDAS-REG'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', '-REG'])
    capas['MEDIDAS-TITULOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'TIT'])
    capas['REGISTRADOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'REGIST'])
    return capas
