from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtCore import QVariant

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
def CheckIntersectionDistance(line_geom):
    """
    Computes the minimum distance of intersection points between the provided geometry and 
    the active layer's selected feature.

    PARAMETERS
    line_geom: QgsGeometry object representing a line geometry

    COMMENTS
    - The function assumes that there is a feature selected in the active layer.
    - It converts the selected feature's geometry to a line and calculates intersections with the provided geometry.

    RETURNS
    Float representing the minimum distance along the provided line geometry to the intersection points
    """
    feature = iface.activeLayer().selectedFeatures()[0]
    distances = []
    perimeter_line = feature.geometry().convertToType(QgsWkbTypes.LineGeometry, False)
    intersection_points = perimeter_line.intersection(line_geom)
    if not intersection_points.isMultipart():
        min_distance = line_geom.lineLocatePoint(intersection_points)
    else:
        for point in intersection_points.asMultiPoint():
            # Obtener la distancia a lo largo de la línea
            distance = line_geom.lineLocatePoint(QgsGeometry.fromPointXY(point))
            distances.append(distance)
            min_distance = min(distances)
    return min_distance
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
