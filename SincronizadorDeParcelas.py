import pandas as pd
from PyQt5.QtCore import QVariant
from qgis.utils import *
from qgis.gui import *
from qgis.core import *

# 'TEST'
# AppendSyncErrorToFeature(iface.activeLayer(), layer.selectedFeatures(), 1)
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
# CheckLayerInMap('Propietarios-PHs')
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
# CheckSelection(iface.activeLayer(), True)
def CheckSelection(layer, onlySelected):
    """
    Checks for features selected in the layer, or any features at all.

    PARAMETERS
    layer: layer feature or string representing a layer name
    onlySelected: boolean

    COMMENTS
    If onlySelected is True, this will return any selected features, or
    False if none selected. If set to false 

    RETURNS
    List of QgsFeatures if features were found
    False if not
    """
    if onlySelected:
        features = layer.selectedFeatures()
        if not features:
            print(f'No selected features in {layer.name()}')
            return False
    else:
        features = [x for x in layer.getFeatures()]
        if not features:
            print(f'Layer {layer.name()} was empty')
            return False
    return features

# 'TEST'
# csvdict = CsvToDictList(r'C:\MaxlocV11\Manzana25.xls', floatFields=['PORCEN','V2','V3','V4'], dropFields_aprox=['EXPTE','ANIO'], fieldNameTranslations={'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'})
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
def IsCompatible(value, fieldType):
    """
    Verifica si el valor es compatible con el tipo de dato esperado por el campo de la capa.
    
    PARAMETROS
    value: Valor a verificar.
    field_type: Tipo de dato esperado por el campo (QVariant.Int, QVariant.Double, etc.).
    
    RETURN
    True si el valor es compatible con el tipo de dato
    False en caso contrario.
    """
    # Comprobaciones de tipo
    if fieldType == QVariant.Int:
        return isinstance(value, int)
    elif fieldType == QVariant.Double:
        return isinstance(value, (int, float))  # Los valores enteros son aceptables en campos de tipo Double
    elif fieldType == QVariant.String:
        return isinstance(value, str)
    elif fieldType == QVariant.Bool:
        return isinstance(value, bool)
    elif fieldType == QVariant.Date:
        # En QGIS, las fechas deben ser objetos de tipo `QDate` o `datetime.date`
        from datetime import date
        return isinstance(value, date)
    elif fieldType == QVariant.DateTime:
        # En QGIS, las fechas y horas deben ser objetos `QDateTime` o `datetime.datetime`
        from datetime import datetime
        return isinstance(value, datetime)
    elif fieldType == QVariant.Time:
        # En QGIS, las horas deben ser objetos `QTime` o `datetime.time`
        from datetime import time
        return isinstance(value, time)
    elif fieldType == QVariant.LongLong:
        return isinstance(value, int)  # `LongLong` es un tipo entero grande
    # Otros tipos de datos específicos pueden agregarse aquí
    else:
        # Para otros tipos, permitir cualquier valor no nulo
        return value is not None

# 'TEST'
def RemoveStartingChars(string,char):
    """
    Removes all leading characters from the input string that match the specified character.

    PARAMETERS
    string: str
        The input string from which to remove leading characters.
    char: str
        The character to remove from the beginning of the input string.

    COMMENTS
    This function iteratively removes the specified character from the start of the string until 
    it encounters a different character or the string becomes empty. It is useful for cleaning up 
    strings that might have unwanted leading characters such as spaces, zeroes, or special symbols.

    RETURNS
    str
        The modified string without leading characters that match the specified character.
        If the input string is entirely composed of the specified character, an empty string 
        is returned.
    """
    while len(string)>0 and string[0] == char:
        string = string[1:]
    return string

def RemoveEndingChars(string, char):
    """
    Removes all trailing characters from the input string that match the specified character.

    PARAMETERS
    string: str
        The input string from which to remove trailing characters.
    char: str
        The character to remove from the end of the input string.

    COMMENTS
    This function iteratively removes the specified character from the end of the string until 
    it encounters a different character or the string becomes empty. It is useful for cleaning up 
    strings that might have unwanted trailing characters such as spaces, zeroes, or special symbols.

    RETURNS
    str
        The modified string without trailing characters that match the specified character.
        If the input string is entirely composed of the specified character, an empty string 
        is returned.
    """
    while len(string)>0 and string[-1] == char:
        string = string[:-1]
    return string

# 'TEST'
# len(SelectDictsFromList(csvdict, {'TEN':'S'}))
def SelectDictsFromList(dictList, matchFilters={}, unmatchFilters={}):
    """
    Filters the list of dictionaries using filter dicts for matching or
    unmatching fields on the dicts.

    PARAMETERS
    dictList: list 
        List made of dictionaries like [{..},{..},..]
    matchFilters: dictionary 
        Desired values in fields
    unmatchFilters: dictionary 
        Undesired values in fields

    COMMENTS

    RETURNS
    List of dictionaries
    Empty list if no match was found
    """
    result = []
    for element in dictList:
        flag = True
        for key, value in matchFilters.items():
            if not value == element[key]:
                flag = False
                break
        for key, value in unmatchFilters.items():
            if value == element[key]:
                flag = False
                break
        if flag:
            result += [element]
    return result

# 'TEST'
# parcdict = SetDictListKey(csvdict, 'NOMENCLA')
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
# SyncFieldsFromDict(iface.activeLayer(), layer.selectedFeatures(), SetDictListKey(csvdict, key), 'NOMENCLA', ['PARTIDA'])
def SyncFieldsFromDict(layer, features, data, keyField, fields=False, ignoreMultiples=False):
    #
    layerFields = [f.name() for f in layer.fields()]
    dictFields = [k for k in next(iter(data.values()))[0].keys()]
    if not fields:
        fields = [f.name() for f in layer.fields()]
        fields.remove(keyField)
    if not keyField in layerFields or not keyField in dictFields:
        print(f'Key field {keyField} was not found on either {layer.name()} or the data source')
        return False
    notFound = []
    for field in fields:
        if not field in layerFields:
            print(f'Field {field} was not found on {layer.name()} and will be ignored')
            notFound += [field]
        if not field in dictFields:
            print(f'Field {field} was not found on data and will be ignored')
            notFound += [field]
    for field in notFound:
        fields.remove(field)
    for feature in features:
        key = feature[keyField]
        if key in data:
            entries = data[key]
            if len(entries) > 1:
                print(f'More than 1 feature with key {key} was found on dictionary.')
                if ignoreMultiples:
                    continue
            entry = entries[0]
            for field in fields:
                with edit(layer):
                    if field in entry: 
                        value = entry[field]
                        fieldType = layer.fields().field(field).type()
                        if IsCompatible(value, fieldType):
                            try:
                                feature[field] = value
                            except Exception as e:
                                print(f"Fallo al copiar {value} a {field}({fieldType}). Errormsg: {e}")
                    else:
                        print(f'Field {field} was not found in')
                    if not layer.updateFeature(feature):
                        print(f"Error al actualizar la entidad con clave {key}. Revertiendo cambios.")
                        layer.rollBack()

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano
def CompletarPartidas(ejido, capa = False, poseedores=False, soloSeleccionados=True):
    """
    Completa los campos especificados de la capa URBANA objetivo con
    los datos leidos desde el csv descargado desde progress. Requiere
    los campos NOMENCLA, CC y TEN para identificar correctamente la 
    parcela. Y PARTIDA, obviamente.

    PARAMETROS
    ejido: numero de ejido de la capa
    capa: QgsVectorLayer o cadena con el nombre de la capa. La misma
        debe estar cargada en el mapa. Por defecto toma la capa activa
        actual.
    poseedores: si se apica poseedores=True, va a filtrar los csv para
        que solo incluyan poseedores. Por defecto, los filtra pero para
        EXCLUIR los poseedores.
    soloSeleccionados: Por defecto actualiza las parcelas seleccionadas
        solamente. Si se aplica soloSeleccionados=False, actualiza toda
        la capa. Puede tomarse su tiempo...

    COMENTARIOS
    Hola, soy un comentario!

    DEVUELVE
    Nada
    """
    #controlo el input de la capa y seleccion
    if capa:
        capa = CheckLayerInMap(capa)
    else:
        capa = iface.activeLayer()

    entidades = CheckSelection(capa, soloSeleccionados)
    if not entidades:
        return

    #controlo que existan los campos que necesito en la capa. asumo que los que vienen de csv estan bien
    for campo in ['NOMENCLA','PARTIDA', 'CC','TEN']:
        if not campo in [x.name() for x in capa.fields()]:
            print(f'La capa {capa.name()} no tenia el campo {campo}' )
            return False

    #obtengo los diccionarios desde disco
    diccionarios = {1:False,2:False,3:False}
    nombrecc = {1:'Chacra',2:'Quinta',3:'Manzana'}
    camposDecimales = ['PORCEN','V2','V3','V4']
    camposBorrarAprox = ['EXPTE','ANIO']
    conversiones = {'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    for cc in [1,2,3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        diccionarios[cc] = CsvToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)
        if poseedores:
            diccionarios[cc] = SelectDictsFromList(diccionarios[cc], matchFilters={'TEN':'S'})
        else:
            diccionarios[cc] = SelectDictsFromList(diccionarios[cc], unmatchFilters={'TEN':'S'})
        diccionarios[cc] = SetDictListKey(diccionarios[cc], 'NOMENCLA')

    #separo las parcelas por cc y matcheo por nomenclatura con el diccionario que le corresponda
    #de momento, esto no tiene en cuenta PHS
    for cc in [1,2,3]: 
        subconjunto = [x for x in entidades if x['CC']==cc]
        SyncFieldsFromDict(capa, subconjunto, diccionarios[cc], 'NOMENCLA', ['PARTIDA'])

def CompletarTabla(ejido, capa = False, soloSeleccionados=True):
    """
    Completa la tabla completa de la capa URBANA objetivo con los datos
    leidos desde el csv descargado desde progress. Por defecto solo lo
    hace a las parcelas seleccionadas.

    PARAMETROS
    ejido: numero del ejido
    capa: cadena o QgsVectorLayer de la capa que se va a completar. Por
        defecto toma la capa actual.
    soloSeleccionados: Por defecto actualiza las parcelas seleccionadas
        solamente. Si se aplica soloSeleccionados=False, actualiza toda
        la capa. Puede tomarse su bueeeen tiempo...

    COMENTARIOS
    Hola, soy un comentario!

    DEVOLUCION
    Nada
    """
    #controlo el input de la capa y seleccion
    if capa:
        capa = CheckLayerInMap(capa)
    else:
        capa = iface.activeLayer()

    seleccion = CheckSelection(capa, soloSeleccionados)
    if not seleccion:
        return

    #controlo que existan los campos que necesito en la capa. asumo que los que vienen de csv estan bien
    for campo in ['PARTIDA', 'CC']:
        if not campo in [x.name() for x in capa.fields()]:
            print(f'La capa {capa.name()} no tenia el campo {campo}' )
            return False

    #obtengo las listas de diccionarios desde disco y los unifico
    diccionario = []
    nombrecc = {1:'Chacra',2:'Quinta',3:'Manzana'}
    camposDecimales = ['PORCEN','V2','V3','V4']
    camposBorrarAprox = ['EXPTE','ANIO']
    conversiones = {'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    for cc in [1,2,3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        diccionario += CsvToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)

    #aplico algunas conversiones a los datos.. parece que solo necesite una
    for entidad in diccionario:
        entidad['MZNA'] = RemoveEndingChars(RemoveStartingChars(entidad['MZNA'], '0'), 'X')

    diccionario = SetDictListKey(diccionario, 'PARTIDA')

    # Blanqueo los valores de COD, DOCUMENTO, APELLIDO y REGISTRO de las entidades
    with edit(capa):
        for entidad in seleccion:
            for campo in ['COD','DOCUMENTO','APELLIDO','REGISTRO']:
                if not campo in [x.name() for x in capa.fields()]:
                    print(f'La capa {capa.name()} no tenia el campo {campo}' )
                else:
                    entidad[campo] = None
            if not capa.updateFeature(entidad):
                print(f"Error al blanquear la capa. Revertiendo cambios.")
                capa.rollBack()
    # Si no se encuentra la partida en el diccionario, es xq no existen
    SyncFieldsFromDict(capa, seleccion, diccionario, 'PARTIDA')
