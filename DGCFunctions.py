"""
DGC Python Functions (23 Oct 2024)
Created for use at DGC with PyQGis, only work in that enviroment due to file structure. Docstrings and variable names are in spanish, as a deference for coworkers that may have to update this someday.
"""
import os
import sys
import urllib.request
import importlib.util
import tempfile
from CommonFunctions import *
DicEjidos = {}

def BuscarCapasUrbanas(numeroDeEjido, reescribirDicEjidos=False):
    """
    Busca y devuelve las rutas de las capas urbanas en el sistema de archivos. Intenta primero buscarlas en el diccionario de ejidos.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        Representa el numero del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.
    reescribirDicEjidos: booleano
        Si se le asigna verdadero, se va directamente a reescribir las direcciones en la global dicEjidos, en vez de intentar leerla.

    COMENTARIOS
    - La función asume que las capas están organizadas en carpetas específicas dentro de una carpeta raíz.
    - Se construyen las rutas a las capas de propietarios y poseedores a partir de la estructura de carpetas.

    RETORNOS
    Un diccionario con las rutas de las capas urbanas, donde las claves son PROPIETARIOS, POSEEDORES, EXPEDIENTES, MANZANAS, RADIOS, CIRCUNSCRIPCIONES, CALLES, MEDIDAS-REG, MEDIDAS-TITUOS y REGISTRADOS.
    """
    global DicEjidos
    n = int(numeroDeEjido)
    if not reescribirDicEjidos:
        if n in DicEjidos.keys():
            if 'PROPIETARIOS' in DicEjidos[n].keys:
                return DicEjidos[n]
    directorioPueblosCADGIS  = r'L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    if not os.path.exists(directorioPueblosCADGIS):
        directorioPueblosCADGIS  = r'C:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    numeroDeEjido = STR_FillWithChars(numeroDeEjido, 3, '0')
    DicEjidos[n]['PROPIETARIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'PROP'])
    DicEjidos[n]['POSEEDORES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'POSE'])
    DicEjidos[n]['EXPEDIENTES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'EXP', 'EXP'])
    DicEjidos[n]['MANZANAS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'MANZ'])
    DicEjidos[n]['RADIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'RADIO'])
    DicEjidos[n]['CIRCUNSCRIPCIONES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CIRC'])
    DicEjidos[n]['CALLES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CALLE'])
    DicEjidos[n]['MEDIDAS-REG'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'REGS'])
    DicEjidos[n]['MEDIDAS-TITULOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'TIT'])
    DicEjidos[n]['REGISTRADOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'REGIST'])
    return DicEjidos[n]

def CompletarDicEjidos(reescribirDicEjidos=False):
    """
    Lee el csv con la informacion de los ejidos desde Github, genera un diccionario y lo enriquece con las direcciones de los archivos shape.

    PARAMETROS

    COMENTARIOS
    - Larga un choclo impresionante de alertas en la consola. Es algo a rever.

    RETORNOS
    Un diccionario con las informacion de los ejidos y las rutas de sus capas.
    """
    global DicEjidos
    DicEjidos = {}
    csvPath = PATH_GetFileFromWeb('InfoEjidos.csv')
    ejidos = CSV_ToDictList(csvPath, separator=';')
    ejidos = DICT_SetKey(ejidos, 'EJIDO')

    for key, value in ejidos.items():
        DicEjidos[key] = value[0]
        DicEjidos[key].update(BuscarCapasUrbanas(key,reescribirDicEjidos))
    return DicEjidos

def LeerDicEjidos():
    global DicEjidos
    return DicEjidos

DicEjidos = CompletarDicEjidos()
print("""Perdon por el spam, te dejo un michi mamadisimo
      A__A
     (•^ •) 
    ＿ノヽ ノ＼＿
`/　`/ ⌒Ｙ⌒ Ｙ  ヽ
( 　(三ヽ人　 /　  |
|　ﾉ⌒＼ ￣￣ヽ   ノ
ヽ＿＿＿＞､＿_／
    ｜( 王 ﾉ〈   
    /ﾐ`ー―彡\  
   / ╰    ╯ \ 


######################################################################################################################################################################################################################################################################################################################################################################################################################################################################   
""")
