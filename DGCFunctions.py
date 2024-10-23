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
def CompletarDicEjidos():
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
    url = f'https://raw.githubusercontent.com/jopaz0/QGis-DGC/refs/heads/main/InfoEjidos.csv'
    tempFolder = tempfile.gettempdir()
    sys.path.append(tempFolder)
    csvPath = os.path.join(tempFolder, f"InfoEjidos.csv")
    if os.path.exists(csvPath):
        os.remove(csvPath)
    urllib.request.urlretrieve(url, csvPath)
    ejidos = CSV_ToDictList(csvPath, enc='utf-8', separator=';',)
    ejidos = DICT_SetKey(ejidos, 'EJIDO')
    for key, value in ejidos.items():
        DicEjidos[key] = value[0]
        DicEjidos[key].update(BuscarCapasUrbanas(key))

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
    if not reescribirDicEjidos:
        n = int(numeroDeEjido)
        if n in DicEjidos.keys():
            return DicEjidos[n]
    directorioPueblosCADGIS  = r'L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    if not os.path.exists(directorioPueblosCADGIS):
        directorioPueblosCADGIS  = r'C:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    numeroDeEjido = STR_FillWithChars(numeroDeEjido, 3, '0')
    capas = {}
    capas['PROPIETARIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'PROP'])
    capas['POSEEDORES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'POLIGONO', 'POSE'])
    capas['EXPEDIENTES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'EXP', 'EXP'])
    capas['MANZANAS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'MANZ'])
    capas['RADIOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'RADIO'])
    capas['CIRCUNSCRIPCIONES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CIRC'])
    capas['CALLES'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'CALLE'])
    capas['MEDIDAS-REG'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'REGS'])
    capas['MEDIDAS-TITULOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'TIT'])
    capas['REGISTRADOS'] = PATH_FindFileInSubfolders(directorioPueblosCADGIS, [numeroDeEjido, 'PUEBLO', 'REGIST'])
    return capas

def GenerarShapeManzanas(ejido, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
   Genera un shape de Manzanas del ejido indicado. Usa como base el shape de parcelas del ejido.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        Representa el numero del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.
    distanciaBuffer: numero 
        La distancia que debe expanderse y contraerse la capa para eliminar cuñas.
    agregarAlLienzo: booleano
        Si se deja en Verdadero, carga la capa al lienzo de QGis.

    COMENTARIOS
    - Se hacen algunos calculos de antes de disolver; unifica los CC de PH con los de parcelas normales, por ejemplo.
    - Luego de disolver, se intenta eliminar anillos y cuñas medainte buffers

    RETORNOS
    - QgsVectorLayer conteniendo la capa si la funcion tuvo exito
    - Falso si ocurrio un error
    """
    try:
        capa = BuscarCapasUrbanas(ejido)['PROPIETARIOS']
        capa = processing.run('native:fixgeometries', {'INPUT': capa, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'INPUT': capa, 'FIELD_LENGTH' : 0, 'FIELD_NAME' : 'CC', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'IF(cc=4,3,if(cc=5,2,cc))', 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
        # Aun no tengo las expresiones cargadas en el mapa
        # capa = processing.run('native:fieldcalculator', { 'FIELD_LENGTH' : 4, 'FIELD_NAME' : 'MZNA', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 2, 'FORMULA' : 'Quitar0(MZNA)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:dissolve', {'INPUT': capa, 'FIELD' : ['EJIDO','CIRC','RADIO','MZNA','CC'], 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer*-1, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa.setName(f'{STR_FillWithChars(ejido,3)}-MANZANAS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar las manzanas del ejido {ejido}. ErrorMSG: {e}')
        return False

def GenerarShapeRegistrados(ejido, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
    Genera un shape de Registrados del ejido indicado. Usa como base el shape de parcelas del ejido.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        Representa el numero del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.
    distanciaBuffer: numero 
        La distancia que debe expanderse y contraerse la capa para eliminar cuñas.
    agregarAlLienzo: booleano
        Si se deja en Verdadero, carga la capa al lienzo de QGis.

    COMENTARIOS
    - Se hacen algunos calculos de antes de disolver; unifica los CC de PH con los de parcelas normales, por ejemplo.
    - Luego de disolver, se intenta eliminar anillos y cuñas medainte buffers

    RETORNOS
    - QgsVectorLayer conteniendo la capa si la funcion tuvo exito
    - Falso si ocurrio un error
    """
    try:
        capas = BuscarCapasUrbanas(ejido)
        capaPropietarios = capas['PROPIETARIOS']
        capaPoseedores = capas['POSEEDORES']
        capa = processing.run('native:mergevectorlayers', { 'CRS' : QgsCoordinateReferenceSystem(''), 'LAYERS' : [capaPropietarios,capaPoseedores], 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fixgeometries', {'INPUT': capa, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        # Aun no tengo las expresiones cargadas en el mapa
        # layer = processing.run('native:fieldcalculator', { 'FIELD_LENGTH' : 4, 'FIELD_NAME' : 'MZNA', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 2, 'FORMULA' : 'Quitar0(MZNA)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'INPUT': capa, 'FIELD_LENGTH' : 0, 'FIELD_NAME' : 'CC', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'IF(cc=4,3,if(cc=5,2,cc))', 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
        capa.setSubsetString('REGISTRADO is not null')
        capa = processing.run('native:dissolve', {'INPUT': capa, 'FIELD' : ['EJIDO','CIRC','RADIO','MZNA','CC','REGISTRADO'], 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer,'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer*-1,'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:addfieldtoattributestable', { 'FIELD_LENGTH' : 2, 'FIELD_NAME' : 'COLOR', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 0, 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'FIELD_LENGTH' : 2, 'FIELD_NAME' : 'COLOR', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'rand(1,25)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa.setName(f'{STR_FillWithChars(ejido,3)}-REGISTRADOS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar los registrados del ejido {ejido}. ErrorMSG: {e}')
        return FalsE

CompletarDicEjidos()