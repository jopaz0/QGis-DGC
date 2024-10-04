import os
import pandas as pd
from PyQt5.QtCore import QVariant
from qgis.utils import *
from qgis.gui import *
from qgis.core import *

# 'TEST'
# layer = iface.activeLayer()
# feature = layer.selectedFeatures()
# AppendSyncErrorToFeature(layer, features, 1)
def AppendSyncErrorToFeature(layer, features, errorCode, errorField='COD'):
    """
    Adds an error code to an entity.

    PARAMETERS
    layer: QgsVectorLayer or similar
    features: list of QgsFeatures belonging to layer
    errorcode: integer
    errorField: string, name of the field where the error code should
        be added

    COMMENTS
    If errorCode is not found on the dictionary, it will default to 
    error 0.
    If errorField is not found in layer, error will be informed trough
    console. It is recommended to blank the field prior to using this,
    because errors are summed up, not replaced, So if there's previous
    data the field will not be useful.
    Errors can be consulted on function Dict_Errors().

    RETURNS
    True if the error was added to the field
    False if the field was not found
    """
    if type(features) is not list:
        features = [features]
    errores = Dict_Errors()
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

# 'TEST'
# layer = 'Propietarios-PHs'
# CheckLayerInMap(layer)
def CheckLayerInMap(layer):
    """
    Checks that the provided layer is loaded on the map canvas.

    PARAMETERS
    layer: layer feature or string representing a layer name

    COMMENTS
    No errors found yet

    RETURNS
    QgsVectorLayer if layer is loaded on map canvas
    False if not
    """
    if type(layer) == str:
        layers = QgsProject.instance().mapLayersByName(layer)
        if not layers:
            print(f"Error, layer '{layer}' was not loaded in the map canvas.")
            return False
        if len(layers) > 1:
            print(f"Alert, there is more than one layer called {layer} on the map canvas.")
        return layers[0]
    if type(layer) == QgsVectorLayer:
        return layer
    print(f"Layer was not typed as a string or QgsVectorLayer.")
    return False

# 'TEST'
# csvPath = r'C:\MaxlocV11\Manzana25.xls'
# fnt = {'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
# ff = ['PORCEN','V2','V3','V4']
# dfa = ['EXPTE','ANIO']
# csvdict = CsvToDictList(csvPath, floatFields=ff, dropFields_aprox=dfa, fieldNameTranslations=fnt)
# print(csvdict[0])
def CsvToDictList(csvPath, 
                  floatFields=[], 
                  dropFields_aprox=[], 
                  dropFields_exact=[], 
                  enc='latin-1', 
                  separator=';',
                  fieldNameTranslations={},
                  fieldsToUppercase=True):
    #There seems to be no need to parse integer fields, but can be added later.
    """
    Converts a text delimited file into a list of dictionaries.

    PARAMETERS
    csvPath: full path to the text file.
    floatFields: list of strings containing names of fields that must
        be parsed to float
    dropFields_aprox: list of strings that are to be compared to fields
        Any field whose name contains any of these will be dropped
    dropFields_exact: list of strings that are to be compared to fields
        Any field whose name is equal to any of these will be dropped
    enc: string containing CSV's encoding. Most CSV files use 'UTF-8'
    separator: string containing CSV's delimiter. Most CSV files use 
        ',' or ';'
    fieldNameTranslations: dictionary containing csv expected field 
        names as keys and the desired output field names as values.
    
    COMMENTS
    Fields not found are ignored. No errors found yet.

    RETURNS
    A list of dictionaries => [{..}{..}{..}]
    """
    data = pd.read_csv(csvPath, encoding=enc, sep=separator, skipinitialspace=True)
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
    csvList = data.to_dict(orient='records')
    return csvList

# 'TEST'
# Dic_Errores()
def Dict_Errors():
    """
    NO PARAMETERS

    COMMENTS
    Key 'CODE' is a power of 2. So when error codes are summed up, the
    error can be deducted mathematically.

    RETURNS
    A dictionary of known errors.
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

# 'TEST'
# dictList = csvdict
# key = 'NOMENCLA'
# parcdict = SetDictListKey(dictList, key)
# for x in parcdict.items():
#     print(x)
#     break
def SetDictListKey(dictList, keyField):
    """
    Takes al list of dictionaries and parses it do a dictionary of
    lists.

    PARAMETERS
    dictList: a list of dictionaries, like [{..},{..},{..}]
    keyField: string, name of the field to be used as key.

    COMMENTS
    If an element doesnt contain the field, we can deduct none of them
    will, so the function will return False.

    RETURNS
    A dictionary with the structure {key: [{..},{..},], key...}
    False if the field was not found
    """
    result = {}
    for entry in dictList:
        if not keyField in entry:
            print(f'An element lacked ')
            return False
        value = entry.get(keyField)
        if value in result:
            result[value].append(entry)
        else:
            result[value] = [entry]
    return result

# 'TEST'
# layer = iface.activeLayer()
# dict = parcdict
# keyField = 'NOMENCLA'
# fields = ['PARTIDA']
# SyncFieldsFromDict(layer, dict, keyField, fields)
def SyncFieldsFromDict(layer, data, keyField, fields=False, selectedOnly=True, ignoreMultiples=False):
    #
    layerFields = [f.name() for f in layer.fields()]
    dictFields = [k for k in next(iter(data.values()))[0].keys()]
    if not fields:
        fields = layerFields
        fields.remove(keyField)
    if not keyField in layerFields or not keyField in dictFields:
        print(f'Key field {keyField} was not found on either {layer.name()} or the data source')
        return False
    notFound = []
    for field in fields:
        if not field in layerFields or not field in dictFields:
            print(f'Field {keyField} was not found on either {layer.name()} or the data source and will be ignored')
            notfound += [field]
    for field in notFound:
        fields.remove(field)
    if selectedOnly:
        features = layer.selectedFeatures()
        if not features:
            print(f'No features selected on {layer.name()}')
            return False
    else:
        features = layer.getFeatures()
    for feature in features:
        key = feature[keyField]
        if key in data:
            entries = data[key]
            if len(entries) > 1:
                print(f'More than 1 feature with key {key} was found on dictionary.')
                if ignoreMultiples:
                    continue
            entry = entries[0]
            with edit(layer):
                for field in fields:
                    if field in entry:
                        feature[field] = int(entry[field])
                    else:
                        print(f'Field {field} was not found in')
                layer.updateFeature(feature)

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###

#Funciones destinadas a uso interno en DGC. O sea, estan en castellano
def CompletarCampos(capa, ejido, targetFields=False):
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
    capa = CheckLayerInMap(capa)
    for cc in [1,2,3]:
        if cc == 3:
            csvPath = f'C:\\MaxlocV11\\Manzana{ejido}.xls'
        elif cc == 2:
            csvPath = f'C:\\MaxlocV11\\Manzana{ejido}.xls'
        else:
            csvPath = f'C:\\MaxlocV11\\Manzana{ejido}.xls'

    if not capa:
        print('No se pudo validar la capa de entrada')
        return
    
    data = 
    SyncFieldsFromDict(capa, data, keyField, fields=False, selectedOnly=True, ignoreMultiples=False)
