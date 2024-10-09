"""
Modulo: Sincronizador de Parcelas (04 Oct 2024)
Funciones registradas: CompletarPartidas, CompletarTabla
Tipee help(funcion) en la consola para mas informacion.

Este script debe reemplazr al anterior sincronizador, que es una 
reverenda poronga. No deberia trabarse tanto si hay demasiadas
entradas en los CSVs de Progress. Pero no informa de los errores
tan detalladamente como el anterior.
"""

import pandas as pd
import os
import processing
from PyQt5.QtCore import QVariant
from qgis.utils import *
from qgis.gui import *
from qgis.core import *



def AddCsvAs(csv_path, name):
    uri = 'file:///'+ csv_path.replace('//','/') +'?delimiter=;'
    layer = QgsVectorLayer(uri, name, 'delimitedtext')
    QgsProject.instance().addMapLayer(layer)
    return layer

def AddLayerFromPath(layerPath):
    layerName = layerPath.split('\\')[-1].split('.')[0]
    layer = QgsVectorLayer(layerPath, layerName, "ogr")
    layer.setName(layerName)
    QgsProject.instance().addMapLayer(layer)

def CSV_Merge(
        root,
        csvFiles, 
        enc='latin-1', 
        separator=';',
        floatFields=[], 
        fieldNameTranslations={}, 
        fieldsToUppercase=True,
        dropFields_aprox=[],
        dropFields_exact=[],
        outputName = 'MergedCSVs'):
    """
    Receives a list of filepaths and return a merged pandas file.
    """
    try:
        data = pd.concat([pd.read_csv(os.path.join(root, file), encoding=enc, sep=separator, skipinitialspace=True) for file in csvFiles], ignore_index=True)
        if fieldsToUppercase:
            
            data.columns = map(str.upper, data.columns)
        translationDict = {col: fieldNameTranslations.get(col, col) for col in data.columns}
        data = data.rename(columns=translationDict)
        for field in dropFields_aprox:
            columns_to_drop = [col for col in data.columns if field in col]
            data = data.drop(columns=columns_to_drop)
        for field in dropFields_exact:
            columns_to_drop = [col for col in data.columns if field == col]
            data = data.drop(columns=columns_to_drop)
        for field in floatFields:
            if field.upper() in data.columns:
                data[field.upper()] = (
                    data[field.upper()]
                    .astype(str)
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .str.strip()
                    .astype(float)
                    .round(2)
                )
        RemoveLayersContaining(outputName)
        output = os.path.join(root, f'{outputName}.csv')
        if os.path.isfile(output):
            os.remove(output)
        data.to_csv(output, index=False, encoding=enc, sep=separator)
        return output
    except Exception as e:
        print(f'Error al procesar los CSV. ErrorMSG: {e}')
        return False
 
def CSV_Split(csvPath, field, value, enc='latin-1', sep=';'):
    try:
        data = pd.read_csv(csvPath, encoding=enc, sep=sep, skipinitialspace=True)
        dataMatch = data[data[field] == value]
        dataOthers = data[data[field] != value]
        os.remove(csvPath)
        baseName = os.path.splitext(csvPath)[0]
        dataMatch.to_csv(f'{baseName} - {field} {value}.csv', index=False)
        dataOthers.to_csv(csvPath, index=False)
        return True
    except Exception as e:
        print(f'Error al dividir el CSV. Mensaje de error: {e}')
        return False


def FillString(string, width, char, insertAtStart=True):
    string = str(string)
    while len(string)<width:
        if insertAtStart:
            string = char + string
        else:
            string = string + char
    return string

   
#saca una capa del canvas, mas flexible
def RemoveLayersContaining(layer_name):
    # Obtener la lista de capas en el proyecto
    layers = QgsProject.instance().mapLayers().values()
    # Iterar sobre las capas para encontrar las que coincidan con el nombre
    for layer in layers:
        if layer_name in layer.name():
            # Remover la capa del proyecto
            QgsProject.instance().removeMapLayer(layer)

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano
def BuscarCapasUrbanas(ejido):
    root = r'C:\Users\Usuario\Documents\Borrar'
    ejido = FillString(ejido, 3, '0')
    capas = {}
    carpetaEjido = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d.startswith(ejido)][0]
    carpetaPoligonos = [os.path.join(carpetaEjido, d) for d in os.listdir(carpetaEjido) if os.path.isdir(os.path.join(carpetaEjido, d)) and 'POLIGONO' in d][0]
    # carpetaExpedientes = [os.path.join(carpetaEjido, d) for d in os.listdir(carpetaEjido) if os.path.isdir(os.path.join(carpetaEjido, d)) and 'EXPEDIENTE' in d][0]
    # carpetaPueblo = [os.path.join(carpetaEjido, d) for d in os.listdir(carpetaEjido) if os.path.isdir(os.path.join(carpetaEjido, d)) and 'PUEBLO' in d][0]

    capas['PROPIETARIOS'] = [os.path.join(carpetaPoligonos, d) for d in os.listdir(carpetaPoligonos) if os.path.isfile(os.path.join(carpetaPoligonos, d)) and 'PROPIETARIO' in d and d.endswith('.shp')][0]
    capas['POSEEDORES'] = [os.path.join(carpetaPoligonos, d) for d in os.listdir(carpetaPoligonos) if os.path.isfile(os.path.join(carpetaPoligonos, d)) and 'POSEEDOR' in d and d.endswith('.shp')][0]
    return capas

def SincronizacionUrbana(ejido):
    #Leo, unifico y modifico los XLS/CSV urbanos descargados
    root = r'C:\MaxlocV11'
    csvFiles = [f'Manzana{ejido}.xls',f'Quinta{ejido}.xls',f'Chacra{ejido}.xls']
    enc = 'latin-1'
    separator=';'
    floatFields=['PORCEN','V2','V3','V4']
    fieldNameTranslations={'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    fieldsToUppercase=True
    dropFields_aprox=['EXPTE','ANIO']
    dropFields_exact=[]
    outputName = 'MergedCSVs'
    csvPath = CSV_Merge(root, csvFiles, enc, separator, floatFields, fieldNameTranslations, fieldsToUppercase, dropFields_aprox, dropFields_exact, outputName)
    # csv = AddCsvAs(csvPath, outputName)
    
    capas = BuscarCapasUrbanas(ejido)
    # propietarios = AddLayerFromPath(capas['PROPIETARIOS'], 'PROPIETARIOS')
    # poseedores = AddLayerFromPath(capas['POSEEDORES'], 'POSEEDORES')

    

def SincronizarTabla(id):
    if type(id) is int:
        SincronizacionUrbana(id)
    elif type(id) is str:
        print('Esto es solo para ejidos! Ingrese un numero de ejido, no una Seccion o lo que sea.')
        return False
        SincronizacionRural(id)
                            

