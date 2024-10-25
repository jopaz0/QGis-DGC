"""
DGC Python Functions (23 Oct 2024)
Created for use at DGC with PyQGis, only work in that enviroment due to file structure. Docstrings and variable names are in spanish, as a deference for coworkers that may have to update this someday.
"""
import os
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from CommonFunctions import *

DicEjidos = {}

def InicializarDicEjidos():
    """
    Inicializa el diccionario de ejidos si esta vacio.
    """
    global DicEjidos
    if not DicEjidos:
        csvPath = PATH_GetFileFromWeb('InfoEjidos.csv')
        ejidos = DICT_SetKey(CSV_ToDictList(csvPath, separator=';'), 'EJIDO')
        DicEjidos = { key: value[0] for key, value in ejidos.items()}
InicializarDicEjidos()

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
            if 'PROPIETARIOS' in DicEjidos[n].keys():
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

def GenerarShapeManzanas(capa, nombre=False, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
    Genera un shape de Manzanas de la capa indicada. 

    PARAMETROS
    capa: QgsVectorLayer
        las capas a ser disueltas
    nombre: cadena de caracteres
        Nombre base de la capa de salida, a la cual se le agrega un sufijo.
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
    if not capa:
        print('Flaco que mierda es eso que me diste? dame parcelas')
        return False
    try:
        nombre = nombre if nombre else capa.name()
        capa = processing.run('native:fixgeometries', {'INPUT': capa, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'INPUT': capa, 'FIELD_LENGTH' : 0, 'FIELD_NAME' : 'CC', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'IF(cc=4,3,if(cc=5,2,cc))', 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
        # Aun no tengo las expresiones cargadas en el mapa
        # capa = processing.run('native:fieldcalculator', { 'FIELD_LENGTH' : 4, 'FIELD_NAME' : 'MZNA', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 2, 'FORMULA' : 'Quitar0(MZNA)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:dissolve', {'INPUT': capa, 'FIELD' : ['EJIDO','CIRC','RADIO','MZNA','CC'], 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer*-1, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa.setName(f'{nombre}-MANZANAS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar las manzanas del ejido {ejido}. ErrorMSG: {e}')
        return False
RehacerMzs = GenerarShapeManzanas
rehacermzs = GenerarShapeManzanas
REHACERMZS = GenerarShapeManzanas

def GenerarShapeRegistrados(capas, nombre=False, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
    Genera un shape de Registrados de la capa indicada.

    PARAMETROS
    capas: lista
        las capas a ser disueltas
    nombre: cadena de caracteres
        Nombre base de la capa de salida, a la cual se le agrega un sufijo.
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
    for capa in capas:
        if not capa:
            print('Flaco que mierda es eso que me diste? dame parcelas')
            return False
    try:
        nombre = nombre if nombre else capa.name()
        capa = processing.run('native:mergevectorlayers', { 'CRS' : QgsCoordinateReferenceSystem(''), 'LAYERS' : capas, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
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
        capa.setName(f'{nombre}-REGISTRADOS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar los registrados del ejido {ejido}. ErrorMSG: {e}')
        return FalsE
RehacerRegs = GenerarShapeRegistrados
rehacerregs = GenerarShapeRegistrados
REHACERREGS = GenerarShapeRegistrados

def LeerDicEjidos():
    """
    Retorna el valor actual de DicEjidos.
    """
    global DicEjidos
    return DicEjidos