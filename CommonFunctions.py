"""
Common Python Functions (09 Oct 2024)
Created for use at DGC with PyQGis, but general enough to implement in other projects.
"""

import os
import pandas as pd
from qgis.core import QgsVectorLayer, QgsProject

def CANVAS_AddLayer(layer, name=False, delimiter=False):
    """
    Adds a specified layer to the map canvas in QGIS.

    PARAMETERS
    layer: Can be a QgsVectorLayer object or a string representing the path to the file.
           If a string is provided, it will be converted to a QgsVectorLayer using the function PathToLayer.
    name: Optional string to specify the layer's name when loading it from a file path.
    delimiter: Optional delimiter string for delimited text files (e.g., CSV). This parameter is only used
               when loading layers from file paths that require a delimiter.

    COMMENTS
    - If a file path is provided as 'layer', the function attempts to load it as a QgsVectorLayer.
    - If a QgsVectorLayer is provided, it will be added directly to the map canvas.
    - Any errors encountered during the loading process will be caught and printed.

    RETURNS
    QgsVectorLayer if the layer is successfully added to the map canvas.
    False if there is an error during the loading process.
    """

    try:
        if type(layer) is str:
            layer = PathToLayer(layer, name, delimiter)
        QgsProject.instance().addMapLayer(layer)
        return layer
    except Exception as e:
        print(f'Exception while loading layer {str(layer)} to map canvas @ CANVAS_AddLayer. ErrorMSG: {e}')
        return False

def CANVAS_CheckForLayer(layer):
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
    try:
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
    except Exception as e:
        print(f'Exception while checking for layer {str(layer)} in map canvas, @ CANVAS_CheckForLayer. ErrorMSG: {e}')
        return False
    print(f"Unexpected error while checking for layer {str(layer)} in map canvas, @ CANVAS_CheckForLayer. Unexpected layer format?")
    return False

def CANVAS_RemoveLayer(layerName):
    """
    Removes a layer from the QGIS map canvas that matches the specified name string.

    PARAMETERS
    layerName: String representing the layer name to search.

    COMMENTS
    - The function iterates through all layers in the current QGIS project.
    - If a layer's name matches the specified string, it is removed from the map canvas.
    - Removes all matching layers

    RETURNS
    None
    """
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layerName == layer.name():
            QgsProject.instance().removeMapLayer(layer)

def CANVAS_RemoveLayersContaining(layerName):
    """
    Removes layers from the QGIS map canvas that contain the specified name substring.

    PARAMETERS
    layerName: String representing the substring to search for in layer names.

    COMMENTS
    - The function iterates through all layers in the current QGIS project.
    - If a layer's name contains the specified substring, it is removed from the map canvas.
    - Removes all matching layers

    RETURNS
    None
    """
    layers = QgsProject.instance().mapLayers().values()
    for layer in layers:
        if layerName in layer.name():
            QgsProject.instance().removeMapLayer(layer)

def CSV_DivideByFieldValue(csvPath, field, value, enc='latin-1', separator=';'):
    """
    Splits a CSV file into two separate files based on a specified field value.

    PARAMETERS
    csvPath: String representing the full path to the CSV file to be split.
    field: String representing the name of the field to filter the data.
    value: Value used to filter the rows of the CSV.
    enc: Optional; String representing the encoding of the CSV file (default is 'latin-1').
    sep: Optional; String representing the delimiter used in the CSV file (default is ';').

    COMMENTS
    - The function reads the CSV file and creates two new files:
      1. One containing rows where the specified field matches the given value.
      2. Another containing all other rows.
    - The original CSV file is removed after processing.

    RETURNS
    Dictionary containing paths to the two CSV files:
    - 'MATCH': path to the file containing matching rows.
    - 'OTHERS': path to the file containing non-matching rows.
    False if there was an exception during processing.
    """
    try:
        data = pd.read_csv(csvPath, encoding=enc, sep=separator, skipinitialspace=True)
        dataMatch = data[data[field] == value]
        dataOthers = data[data[field] != value]
        os.remove(csvPath)
        baseName = os.path.splitext(csvPath)[0]
        matchFilePath = f'{baseName} - {field} {value}.csv'
        dataMatch.to_csv(matchFilePath, index=False, encoding=enc, sep=separator)
        dataOthers.to_csv(csvPath, index=False, encoding=enc, sep=separator)
        return {'MATCH': matchFilePath,'OTHERS': csvPath}
    except Exception as e:
        print(f'Exception while splitting csv file, @ CSV_DivideByFieldValue. ErrorMSG: {e}')
        return False
    finally:
        if 'data' in locals():
            del data
        if 'dataMatch' in locals():
            del dataMatch
        if 'dataOthers' in locals():
            del dataOthers

def CSV_MergeFiles(
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
    Merges multiple CSV files into a single CSV file and applies various transformations.

    PARAMETERS
    root: String representing the directory where the CSV files are located.
    csvFiles: List of strings representing the file names of the CSV files to be merged.
    enc: Optional; String representing the encoding of the CSV files (default is 'latin-1').
    separator: Optional; String representing the delimiter used in the CSV files (default is ';').
    floatFields: Optional; List of strings representing the names of fields to be converted to float.
    fieldNameTranslations: Optional; Dictionary mapping original field names to new names for renaming.
    fieldsToUppercase: Optional; Boolean indicating whether to convert all field names to uppercase (default is True).
    dropFields_aprox: Optional; List of strings representing field names to be approximately dropped from the resulting DataFrame.
    dropFields_exact: Optional; List of strings representing field names to be exactly dropped from the resulting DataFrame.
    outputName: Optional; String representing the name for the merged output CSV file (default is 'MergedCSVs').

    COMMENTS
    - The function reads the specified CSV files, merges them, and performs various transformations such as renaming,
      dropping fields, and converting certain fields to float format.
    - It checks for an existing output file and removes it if necessary before saving the merged result.

    RETURNS
    String representing the path to the merged CSV file if successful.
    False if there was an exception during the merging process.
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
        CANVAS_RemoveLayersContaining(outputName)
        output = os.path.join(root, f'{outputName}.csv')
        if os.path.isfile(output):
            os.remove(output)
        data.to_csv(output, index=False, encoding=enc, sep=separator)
        return output
    except Exception as e:
        print(f'Exception while merging csv files, @ CSV_MergeFiles. ErrorMSG: {e}')
        return False
    finally:
        if 'data' in locals():
            del data

def STR_FillWithChars(string, width, char, insertAtStart=True):
    """
    Fills a string with a specified character until it reaches the desired width.

    PARAMETERS
    string: The original string to be filled.
    width: Integer representing the target length of the string after filling.
    char: String representing the character to use for filling.
    insertAtStart: Optional; Boolean indicating whether to insert the character at the start 
                   (True) or at the end (False) of the string. Default is True.

    COMMENTS
    - The function converts the input to a string and adds the specified character until 
      the length of the string matches the given width.

    RETURNS
    String filled with the specified character to reach the desired width.
    """
    string = str(string)
    while len(string)<width:
        if insertAtStart:
            string = char + string
        else:
            string = string + char
    return string

def PathToLayer(path, name=False, delimiter=';'):
    """
    Converts a file path to a QgsVectorLayer based on its extension.

    PARAMETERS
    path: String representing the path to the file (e.g., 'C:/path/to/file.shp').
    name: Optional string representing the name of the layer in QGIS. If not provided, the file name (without extension) will be used.
    delimiter: Optional delimiter character for CSV or delimited text files (e.g., ',' for CSV). This parameter is only required for .csv and .xls files. Defaults to ';'

    COMMENTS
    - Supports shapefiles (.shp), CSV files (.csv), and Excel files (.xls).
    - The function assumes that the specified path is valid and accessible.
    - If the file extension is not supported or an error occurs, it will print an error message and return False.

    RETURNS
    QgsVectorLayer if the file is successfully converted and added to QGIS.
    False if an error occurs or the file format is not supported.
    """
    try:
        layerName = name if name else path.split('\\')[-1].split('.')[0]
        ext = os.path.splitext(path)[1]
        if ext in ['.csv', '.xls']:
            uri = 'file:///'+ path.replace('//','/') +'?delimiter=' + delimiter
            layer = QgsVectorLayer(uri, layerName, 'delimitedtext')
        elif ext in ['.shp']:
            layer = QgsVectorLayer(path, layerName, 'ogr')
        else:
            print(f"Unexpected file extension while converting {str(layer)} to QgsLayer, @ PathToLayer. Unexpected layer format?")
            return False
        return layer
    except Exception as e:
        print(f'Exception while converting {str(path)} to QgsLayer, @ PathToLayer. ErrorMSG: {e}')
        return False

def IsValueCompatible(value, fieldType):
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
