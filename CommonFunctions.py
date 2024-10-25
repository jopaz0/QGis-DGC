"""
Common Python Functions (10 Oct 2024)
Created for use at DGC with PyQGis, but general enough to implement in other projects.

COMMENTS:
- Functions starting with CANVAS usually require an open QGis map because they take parameters from active layer and selected features.
- Functions starting with CSV, DICT or STR operate over such variable types. DICT usually operates lists of dicts, but can receive a dict and will cast it into a list.
"""
import sys
import os
import gc
import tempfile
import datetime
import urllib.request
import importlib.util
import pandas as pd
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from PyQt5.QtCore import QVariant, QDate, QDateTime, QTime

#FUNCTIONS stariting with CANVAS usually require an open QGis map because they take parameters from active layer and selected features.

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
        else:
            if name:
                layer.setName(name)
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

def CANVAS_CheckSelection(layer, onlySelected=True):
    """
    Validates if the specified layer has any features based on the selection criteria.

    PARAMETERS
    layer: QgsVectorLayer object. The layer from which features will be checked.
    onlySelected: Boolean indicating whether to consider only selected features or all features in the layer. Default is True.

    COMMENTS
    - If `onlySelected` is True, the function checks if there are any selected features in the layer. If no features are selected, it prints a warning message and returns False.
    - If `onlySelected` is False, it considers all features in the layer. If the layer is empty, it prints a warning message and returns False.
    - The function returns the list of features matching the criteria or False if no features were found.

    RETURNS
    List of features if the specified criteria are met; otherwise, it returns False.

    EXCEPTIONS
    - None explicitly raised, but it prints warning messages to indicate empty layers or lack of selected features.

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

def CANVAS_RemoveLayer(layer):
    """
    Removes a layer from the QGIS map canvas.

    PARAMETERS
    layerName: QgsVectorLayer.

    COMMENTS

    RETURNS
    - True if layer was found and deleted
    - False if layer was not found
    """
    try:
        QgsProject.instance().removeMapLayer(layer)
        return True
    except Exception as e:
        print(f'Exception while removing layer, @ CANVAS_RemoveLayer. ErrorMSG: {e}')
        return False

def CANVAS_RemoveLayerByName(layerName):
    """
    Removes a layer from the QGIS map canvas that matches the specified name string.

    PARAMETERS
    layerName: String representing the layer name to search.

    COMMENTS
    - The function iterates through all layers in the current QGIS project.
    - If a layer's name matches the specified string, it is removed from the map canvas.
    - Removes all matching layers

    RETURNS
    - True if layer was found and deleted
    - False if layer was not found
    """
    try:
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layerName == layer.name():
                QgsProject.instance().removeMapLayer(layer)
    except Exception as e:
        print(f'Exception while removing layer {layerName}, @ CANVAS_RemoveLayerByName. ErrorMSG: {e}')
        return False

def CANVAS_RemoveLayerByPath(path):
    """
    Removes any loaded layer in QGIS that is based on the given file path.
    
    PARAMETERS
    path: String representing the full path of the file used as a layer in QGIS.

    RETURNS
    - True if layer was found and deleted
    - False if layer was not found
    """
    try:
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.source() == path:
                QgsProject.instance().removeMapLayer(layer)
    except Exception as e:
        print(f'Exception while removing layer at {path}, @ CANVAS_RemoveLayerByPath. ErrorMSG: {e}')
        return False

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

def CANVAS_RepathLayer(layerName, layerPath, filters={}, forceCRS=False):
    #filters can be upgraded to support a string with the already built filter. maybe later
    """
    Changes the data source of all layers that contain a string to the provided path.

    PARAMETERS
    layerName: String
        A string wich will be compared to the names of all loaded layers in the map canvas.
    layerPath: String
        The path of the new layer
    filters: Dictionary
        A dictionary of strings, like {nameOfField: valueOfField}
    forceCRS: QgsCoordinateReferenceSystem or False
        If set, and layer's CRS is not WGS84, changes the CRS of the layer to the parameter's value.

    COMMENTS
    - The function iterates through all layers in the current QGIS project, replacing the data source of the ones matching layerName.
    - If filters are set, the layer will be filtered accordingly. Only supports '=' for fields and values, and ' AND ' between each filter.

    RETURNS
    None
    """
    layers = []
    if not layerPath:
        try:
            layer.setDataSource(layerPath, '', 'ogr')
        except:
            pass
        print (f'No layer for {layerName} was found in file system.')
        return False
    try:
        for layer in QgsProject.instance().mapLayers().values():
            if layerName.upper() in layer.name().upper():
                layers.append(layer)
        if len(layers) < 1:
            print (f'No layer matching {layerName} was found in map.')
            return False
        if filters:
            expression = ' AND '.join([f"{f}={filters[f]}" if isinstance(filters[f], (int, float)) else f"{f}='{filters[f]}'" for f in filters])
        for layer in layers:
            name = layer.name()
            layer.setDataSource(layerPath, name, 'ogr')
            if filters:
                layer.setSubsetString(expression)
                print(f'Layer {name} datasource changed to {os.path.basename(layerPath)} and filtered with {expression}.')
            else:
                print(f'Layer {name} datasource changed to {os.path.basename(layerPath)}.')
        if forceCRS:
            if not layer.crs().authid() == "EPSG:4326":
                layer.setCrs(forceCRS)
            else:
                print(f'Warning, layer {layer.name()} was set to WGS84.')
        return True
    except Exception as e:
        print (f'Error while changing datsource on layer {layerName} to {layerPath}. ErrorMSG: {e}')
        return False

def CANVAS_ZoomToSelectedFeatures(layer):
    """
    Zooms to selected features in layer, if any.

    PARAMETERS
    layere: QgsVectorLayer
        The layer containing the selected features

    COMMENTS

    RETURNS
    """
    try:
        extent = layer.boundingBoxOfSelected()
        if not extent.isEmpty():
            iface.mapCanvas().setExtent(extent)
            iface.mapCanvas().refresh()
    except:
        print('No features selected to zoom into.')

def CSV_ToDictList(csvPath, 
                  floatFields=[], 
                  dropFields_aprox=[], 
                  dropFields_exact=[], 
                  enc='latin-1', 
                  separator=';',
                  fieldNameTranslations={},
                  fieldsToUppercase=True):
    """
    Converts a CSV file into a list of dictionaries, allowing for data transformations such as field renaming, field dropping, and numeric formatting.

    PARAMETERS
    csvPath: String representing the path to the CSV file to be converted.
    floatFields: List of field names that should be converted to float type. These fields will undergo additional transformations to ensure they are in a consistent format.
    dropFields_aprox: List of substrings. Any field name in the CSV that contains one of these substrings will be dropped.
    dropFields_exact: List of exact field names. Any field with a name that matches an item in this list will be dropped.
    enc: String representing the file's encoding. Default is 'latin-1'.
    separator: String representing the CSV separator. Default is ';'.
    fieldNameTranslations: Dictionary to rename CSV columns. Keys are original column names, values are the new names to be assigned.
    fieldsToUppercase: Boolean indicating whether to convert field names to uppercase. Default is True.

    COMMENTS
    - The function first reads the CSV using pandas, with initial transformations such as renaming and dropping fields.
    - It supports renaming columns based on the `fieldNameTranslations` parameter.
    - Fields in `floatFields` are processed to ensure proper float formatting, replacing comma with a dot and rounding to two decimals.
    - If `fieldsToUppercase` is set to True, all field names are converted to uppercase.

    RETURNS
    List of dictionaries where each dictionary corresponds to a row in the CSV, with the appropriate transformations applied.
    False if cant find the csv or any exception is raised

    EXCEPTIONS
    - Raises FileNotFoundError if `csvPath` does not exist.
    - Raises ValueError if there are issues during the float conversion or if the CSV is malformed.

    """
    try:
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
    except Exception as e:
        print(f'Error al leer el CSV (no existe {csvPath}?). ErrorMSG: {e}')
        return False

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
    CANVAS_RemoveLayerByPath(csvPath)
    try:
        data = pd.read_csv(csvPath, encoding=enc, sep=separator, skipinitialspace=True)
        dataMatch = data[data[field] == value]
        dataOthers = data[data[field] != value]
        os.remove(csvPath)
        baseName = os.path.splitext(csvPath)[0]
        matchFilePath = f'{baseName} - {field} {value}.csv'
        CANVAS_RemoveLayerByPath(matchFilePath)
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
        gc.collect()

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
        gc.collect()

def DICT_Filter(dictList, matchFilters={}, unmatchFilters={}):
    """
    Filters a list of dictionaries based on specified matching and unmatching conditions.

    PARAMETERS
    dictList: List of dictionaries to be filtered. Each dictionary should have the same set of keys.
    matchFilters: Dictionary representing key-value pairs that must be matched in the dictionaries. If a key-value pair is present in `matchFilters`, only dictionaries with the same key-value pair will be included in the result.
    unmatchFilters: Dictionary representing key-value pairs that must *not* be matched in the dictionaries. If a key-value pair is present in `unmatchFilters`, dictionaries with the same key-value pair will be excluded from the result.

    COMMENTS
    - The function iterates through `dictList` and evaluates each dictionary against the criteria in `matchFilters` and `unmatchFilters`.
    - If a dictionary satisfies all conditions in `matchFilters` and does not match any conditions in `unmatchFilters`, it is included in the `result` list.

    RETURNS
    List of dictionaries that meet the criteria defined by `matchFilters` and `unmatchFilters`.

    EXCEPTIONS
    - If any key in `matchFilters` or `unmatchFilters` is not present in the dictionaries of `dictList`, a KeyError will be raised.

    """
    if isinstance(dictList, dict):
        dictList = list(dictList.values())
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

def DICT_SetKey(dictList, keyField):
    """
    Organizes a list of dictionaries or a dictionary of dictionaries into a new dictionary using the specified field as the key.

    PARAMETERS
    dictList: List of dictionaries or Dictionary of dictionaries.
        - If a list is provided, it will be reorganized based on the specified keyField.
        - If a dictionary of dictionaries is provided, it will be converted into a list of dictionaries before processing.
    keyField: String.
        The field in the dictionary to be used as the key for the new dictionary.

    COMMENTS
    - If a dictionary of dictionaries is provided, it will be transformed into a list of dictionaries using only the values.
    - Each dictionary in dictList must contain the keyField; otherwise, the function will terminate and return False.
    - If multiple dictionaries share the same keyField value, they are grouped together in a list under that key.
    - This function is useful for grouping elements by specific attributes (e.g., grouping a list of parcels by their zone code).

    RETURNS
    A dictionary where each key corresponds to a unique value in keyField, and its value is a list of dictionaries that share that keyField value.

    EXCEPTIONS
    - If a dictionary in dictList does not contain keyField, the function returns False and prints a message to the console.
    """
    if isinstance(dictList, dict):
        dictList = list(dictList.values())
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

def PATH_FindFileInSubfolders(rootFolder, filters, ext='.shp'):
    """
    Navigates a folder following the given filters, returns any file matching the last filter and the given extension.

    PARAMETROS
    rootFolder: String 
        Self explanatory
    filters: List
        Contains a list of strings that are to be compared to the contents of the folder and subfolders, secuencially
    ext: String
        Extension of the file to be returned

    COMMENTS

    RETURNS
        String containing the filepath of the first match.
    """
    try:
        subfolder = rootFolder
        for filter in filters[:-1]:
            subfolder = [os.path.join(subfolder, d) for d in os.listdir(subfolder) if os.path.isdir(os.path.join(subfolder, d)) and filter in d.upper()]
            if not subfolder:
                print(f'Alert, there is no folder in {subfolder} that matches {filter}.')
                return False
            if len(subfolder) > 1:
                print(f'Alert, there is more than one folder in {subfolder} that matches {filter}.')
            subfolder = subfolder[0]
        match = [os.path.join(subfolder, d) 
                for d in os.listdir(subfolder) 
                if os.path.isfile(os.path.join(subfolder, d)) and 
                filters[-1] in d.upper() and 
                d.lower().endswith(ext)]
        if not match:
            print(f'Alert, there is no file in {subfolder} that matches {filter}.')
            return False
        elif len(match) > 1:
            print(f'Alert, there is more than one file on {subfolder} that matches {filters[-1]}.')
        return match[0]
    except Exception as e:
        print(f'Error while looking for {filter} in {subfolder}. ErrorMSG: {e}')
        return False

def PATH_GetFileFromWeb(filename, urlRoot=f'https://raw.githubusercontent.com/jopaz0/QGis-DGC/refs/heads/main/'):
    """
    Tryes to retrieve a file from the web, by defaults searchs for it in this Github repo.

    PARAMETROS
    filename: String 
        Self explanatory
    urlRoot: String
        The part of the URL that is not the filename (duh)

    COMMENTS

    RETURNS
        - String containing the filepath of the downloaded file
        - False if failed to get the file
    """
    try:
        tempFolder = tempfile.gettempdir()
        filePath = os.path.join(tempFolder, filename)
        url = urlRoot + urllib.parse.quote(filename)
        if os.path.exists(filePath):
            os.remove(filePath)
        response = urllib.request.urlretrieve(url, filePath)
        if type(response) is tuple:
            return response[0]
        return response
    except Exception as e:
        print(f"Error al descargar {filename}: {e}")
        return False

def GEOM_DeleteDuplicatePoints(geometry, tolerance=0.01):
    """
    Recursively extracts the points from a polygon or multipolygon geometry, preserving the ring structure.

    PARAMETERS
    geometry: QgsGeometry
        The input polygon or multipolygon geometry.
    tolerance: float
        The minimum distance between points to be considered distinct.

    RETURNS
    QgsGeometry
        A geometry matching the input with duplicate points removed.
    """
    try:
        cleaned_geometries = []

        if geometry.isMultipart():
            for part in geometry.asMultiPolygon():
                cleaned_polygon = GEOM_DeleteDuplicatePoints(QgsGeometry.fromPolygonXY(part), tolerance)
                cleaned_geometries.append(cleaned_polygon)
            return QgsGeometry.fromMultiPolygonXY([polygon.asPolygon() for polygon in cleaned_geometries])
        else:
            rings = geometry.asPolygon()
            cleaned_rings = []
            for ring in rings:
                clean_points = []
                last_point = None
                for point in ring:
                    if last_point is None or QgsPointXY(last_point).distance(QgsPointXY(point)) > tolerance:
                        clean_points.append(QgsPointXY(point))
                    last_point = QgsPointXY(point)
                cleaned_rings.append(clean_points)
            return QgsGeometry.fromPolygonXY(cleaned_rings)
    except Exception as e:
        print(f'Warning, geometry could not be cleaned @GEOM_DeleteDuplicatePoints. ErrorMSG: {e}')
        return geometry

def STR_FillWithChars(string, width, char='0', insertAtStart=True):
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

def STR_GetTimestamp(includeMs = False, justDay = False):
    """
    Generates a timestamp string formatted as 'YYYY-MM-DD HH-MM-SS-SSS'.

    PARAMETERS
    includeMs: Optional; Boolean indicating whether to include milliseconds in the timestamp. 
               Default is False.
    justDay: Optional; Boolean indicating whether to return only the date part ('YYYY-MM-DD'). 
              Default is False.

    COMMENTS
    - The function retrieves the current date and time, formatting it according to the specified 
      parameters. If `justDay` is True, it returns only the date in 'YYYY-MM-DD' format.
    - If `includeMs` is True, milliseconds will be included in the format.
    - If justDay is True, includeMs will be ignored

    RETURNS
    String representing the formatted timestamp.
    """

    time = datetime.datetime.now()
    year = str(time.year)
    month = STR_FillWithChars(time.month,2)
    day = STR_FillWithChars(time.day,2)
    if justDay:
        return f'{year}-{month}-{day}'
    hour = STR_FillWithChars(time.hour,2)
    minute = STR_FillWithChars(time.minute,2)
    if not includeMs:
        return f'{year}-{month}-{day} {hour}-{minute}'
    sec = STR_FillWithChars(time.second,2)
    ms = STR_FillWithChars(time.microsecond // 1000, 3)
    return f'{year}-{month}-{day} {hour}-{minute} {sec}-{ms}'

def STR_IntToRoman(num):
    """
    Converts an integer to its Roman numeral representation.

    PARAMETERS
    num: Integer
        The integer to convert to a Roman numeral. Must be in the range from 1 to 3999.

    RETURNS
    String
        The Roman numeral representation of the input integer.

    COMMENTS
    - The function handles integers within the specified range (1 to 3999) as Roman numerals 
      do not have a standard representation for zero or negative numbers.
    - The conversion follows standard Roman numeral conventions.
    """

    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV","I"]
    roman_num = ""
    i = 0
    # Construir el número romano
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def STR_RemoveEndingChars(string, char):
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
    string = str(string)
    while len(string)>0 and string[-1].upper() == char:
        string = string[:-1]
    return string

def STR_RemoveStartingChars(string,char):
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
    string = str(string)
    while len(string)>0 and string[0].upper() == char:
        string = string[1:]
    return string

def STR_IntToRoman(num):
    """
    Converts a Roman numeral string to its integer representation.

    PARAMETERS
    s: String
        The Roman numeral string to convert. Must be a valid Roman numeral.

    RETURNS
    Integer
        The integer representation of the input Roman numeral.

    COMMENTS
    - The function processes the Roman numeral string from right to left, applying the rules
      of Roman numeral subtraction and addition.
    - Valid Roman numerals should follow standard conventions; otherwise, the function may 
      produce incorrect results.
    """
    values = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000
    }
    total = 0
    prevValue = 0
    for char in reversed(num):
        currentValue = values[char]
        if currentValue < prevValue:
            total -= currentValue
        else:
            total += currentValue
        prevValue = currentValue
    return total

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

def SyncFieldsFromDict(layer, features, data, keyField, fields=False, ignoreMultiples=False):
    """
    Synchronizes field values between a QGIS layer and an external data dictionary.

    PARAMETERS
    layer: QgsVectorLayer object representing the target layer where attributes will be updated.
    features: QgsFeatureIterator or list of QgsFeature objects representing the features to be updated.
    data: Dictionary containing feature data. The keys should match the values in the key field, and each key maps to a list of dictionaries representing attribute values.
    keyField: String representing the name of the key field used to match features between the layer and the data dictionary.
    fields: List of field names to be synchronized. If not provided, all fields in the layer except the key field will be used.
    ignoreMultiples: Boolean indicating whether to skip updates when multiple entries in `data` share the same key. Defaults to False.

    COMMENTS
    - This function assumes that `data` is structured such that `data[key]` returns a list of dictionaries, where each dictionary represents attribute values for a corresponding feature.
    - If `ignoreMultiples` is set to False, and a key is found more than once in the data dictionary, a warning will be printed but the update will proceed using the first entry.

    RETURNS
    Boolean indicating whether the synchronization was successful. Returns False if the key field is not found in the layer or the data source, or if any feature update fails.

    EXCEPTIONS
    - Captures and prints errors related to updating feature attributes or mismatched data types.
    - If a feature update fails, it attempts to revert changes and stops the process for that feature.

    """
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
    if not layer.isEditable():
        layer.startEditing()
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
                if field in entry: 
                    value = entry[field]
                    fieldType = layer.fields().field(field).type()
                    if IsValueCompatible(value, fieldType):
                        try:
                            feature[field] = value
                        except Exception as e:
                            print(f"Fallo al copiar {value} a {field}({fieldType}). Errormsg: {e}")
                else:
                    print(f'Field {field} was not found in')
                if not layer.updateFeature(feature):
                    print(f"Error al actualizar la entidad con clave {key}. Revertiendo cambios.")
                    layer.rollBack()

