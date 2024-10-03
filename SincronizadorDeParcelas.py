import os
import pandas as pd
from PyQt5.QtCore import QVariant
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from qgis import processing

# layer = iface.activeLayer()
# feature = layer.selectedFeatures()[0] if layer.selectedFeatureCount() > 0 else None
# features = layer.selectedFeatures() if layer.selectedFeatureCount() > 0 else None

def CheckLayerInMap(layer):
    if type(layer) == str:
        layers = QgsProject.instance().mapLayersByName(layer)
        if not layers:
            return False
        if len(layers) > 1:
            print(f'Cuidado, hay mas de una capa llamada {layer}')
        return layers[0]
    if type(layer) == QgsVectorLayer:
        return layer
    print(f'La capa no era un formato aceptado (QgsVectorLayer)')
    return False

# CsvToDictList(csvPath, keyField, floatFields=['PORCEN','V2','V3','V4'], dropFields = ['EXPTE','ANIO'])
def CsvToDictList(csvPath, keyField, keyType = str, floatFields=[], dropFields=[], enc='latin-1', separator=';'):
    data = pd.read_csv(csvPath, encoding=enc, sep=separator, skipinitialspace=True)
    data.columns = map(str.upper, data.columns)
    for field in dropFields:
        columns_to_drop = [col for col in data.columns if field in col]
        data = data.drop(columns=columns_to_drop)
    for field in floatFields:
        # Si el campo existe en el dataframe, se procesa
        if field.upper() in data.columns:
            data[field.upper()] = (
                data[field.upper()]
                .astype(str)  # Convertir a string para procesar valores con coma y espacios
                .str.replace('.', '')  # Quitar puntos
                .str.replace(',', '.')  # Reemplazar coma por punto decimal
                .str.strip()  # Eliminar espacios en blanco al principio y al final
                .astype(float)  # Convertir a float
                .round(2)  # Redondear a 2 decimales
            )
    csvList = data.to_dict(orient='records')
    return csvList

def Dict_Errores():
    """
    Devuelve un diccionario con los errores definidos.
    """
    # Los nuevos errores deberian tener codigos nuevos, no tocar los codigos ya definidos porque se hace ensalada.
    # Cargar esto a un csv/xls e importarlo desde disco
    errores = { 0: {'RESUMEN': 'Error no documentado. ', 'DESCRIPCION': ''},
                1: {'RESUMEN': 'Partida no encontrada. ', 'DESCRIPCION': ''},
                2: {'RESUMEN': 'Nomencla actual y prev no coinciden. ', 'DESCRIPCION': ''},
                3: {'RESUMEN': 'Multiples parcelas con = Nomencla. ', 'DESCRIPCION': ''},
                4: {'RESUMEN': 'No hay parcelas con esta Nomencla. ', 'DESCRIPCION': ''},
                }
    for error in errores.keys():
        errores[error]['CODE'] = 2**error
    return errores

def AppendSyncErrorToFeature(layer, features, errorCode, errorField='COD'):
    """
    Añade a una entidad un codigo y un mensaje de error.

    layer <= QgsVectorLayer o similar
    features <= lista de QgsFeatures o similar, pertenecientes a la capa
    errorcode <= int
    errorfields <= [str,str] siendo ambos string los campos donde debe 
        guardar los mensajes de error. El primer campo guarda el codigo,
        y el segundo el mensaje, por lo que debiera ser tipo cadena.

    Si no encuentra el campo para el codigo o mensaje, lo informa en 
    consola. Se recomienda MUCHO reiniciar el campo errorCode antes de 
    utilizar esta funcion; si el campo ya contenia valores, los errores 
    nuevos se sumaran y el informe no sera util.

    Los errores se pueden consultar invocando la funcion Dict_Errores().
    """
    if type(features) is not list:
        features = [features]
    errores = Dict_Errores()
    if not errorCode in errores.keys():
        errorCode = 0
    else:
        errorCode = errores[errorCode]['CODE']
        errorMsg = errores[errorCode]['RESUMEN']
    try:
        layerFields = [f.name() for f in layer.fields()]
        if errorField in layerFields:
            with edit(layer):
                for feature in features:
                    if not feature[errorField]:
                        feature[errorField] = 0
                    feature[errorField] += errorCode
                    layer.updateFeature(feature)
        else:
            print(f'El campo {errorField} no existe en la capa. (Error {errorCode}: {errorMsg})')
            return False
        return True
    except Exception as e:
        print(e)
    return False

def 

def CompletarCampos(layer, sourceDict, layerIdField, dictIdField, targetFields=False):
    """
    Completa los campos especificados de la capa objetivo con
    los datos leidos desde el diccionario.

    layer <= QgsVectorLayer o similar
    sourceDict <= diccionario de entidades. Debe tener un formato 
        especifico similar a {key :[{}{}...], ...}
        Se entiende que en algunos casos, una coleccion de entidades
        puede tener mas de una entidad con el mismo identificador,
        por lo que cada key esta vinculado a una lista de dicciona-
        rios en vez de uno singular
        Cada diccionario dentro de esta lista debe poseer pares clave-
        valor representando los campos de la tabla.
    layerIdField <= Identificador en la tabla de la capa
    dictIdField <= Identificador en el diccionario
    targetFields <= Campos a completar. Si no se especifica, toma los
        campos de la capa, exceptuando al identificador.
    """
    layer = CheckLayerInMap(layer)
    if not layer:
        print('No se pudo validar la capa de entrada')
        return
