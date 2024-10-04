"""
Modulo: Numerador de Parcelas (04 Oct 2024)
Funciones registradas: NumerarParcelas
Tipee help(funcion) en la consola para mas informacion.
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from qgis.PyQt.QtCore import Qt

# Variables para configurar
starting_number = 1  # Número inicial, modificar según sea necesario
target_field = "PARCELA"  # Campo de la entidad donde se almacenará el número
numeracion_tool = None
# Crear clase para manejar la herramienta de trazado de línea y numeración
class LineParcelNumberingTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, layer, starting_number, target_field, concat):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.current_number = starting_number
        self.target_field = target_field
        self.concat = concat
        self.points = []  # Almacena los puntos para crear la línea
        self.setCursor(Qt.CrossCursor)  # Cambiar el cursor al cruz cuando se active la herramienta
        self.rubberBand = None
        print(f"""Herramienta de numeración activada:
 Capa = '{layer.name()}'
 Campo = '{target_field}'
 Numero inicial = {starting_number},
 Concatenar con datos previos = {concat}
""")

    def canvasPressEvent(self, event):
        # Capturar las coordenadas donde se hizo clic
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        self.points.append(point)
        
        # Dibujar un punto en el lienzo para indicar los puntos seleccionados
        if len(self.points) >= 1:
            self.rubberBand.addPoint(point, True)  # Añadir puntos a la goma elástica para mostrar la línea

        #print(f"Punto añadido: {point.x()}, {point.y()}")

    def canvasReleaseEvent(self, event):
        # No realizar ninguna acción en la liberación del clic del mouse
        pass

    def keyPressEvent(self, event):
        # Cuando se presiona Enter (key 16777220), se dibuja la línea y se asignan números
        if event.key() == Qt.Key_Return:
            if len(self.points) < 2:
                print("Se necesitan al menos dos puntos para trazar una línea.")
                return
            
            # Crear una geometría de línea a partir de los puntos seleccionados
            line_geom = QgsGeometry.fromPolylineXY(self.points)
            
            #print("Línea creada con éxito. Verificando intersecciones...")
            
            # Asegurar que el CRS de la geometría y la capa sean el mismo
            if self.layer.crs() != self.canvas.mapSettings().destinationCrs():
                #print("Advertencia: CRS de la capa y la línea no coinciden. Transformando geometría de línea...")
                line_geom.transform(QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(), self.layer.crs(), QgsProject.instance()))
            
            # Crear un índice espacial para la capa (esto ayuda a mejorar la detección de intersecciones)
            spatial_index = QgsSpatialIndex(self.layer.getFeatures())
            
            # Encontrar entidades que potencialmente intersecten la línea usando el índice espacial
            intersecting_ids = spatial_index.intersects(line_geom.boundingBox())
            
            #print(f"Entidades potencialmente intersectadas: {len(intersecting_ids)}")
            
            if not intersecting_ids:
                print("No se encontraron entidades cercanas a la línea trazada.")
                return

            # Filtrar solo las entidades que realmente intersectan la línea
            intersecting_features = [f for f in self.layer.getFeatures(QgsFeatureRequest().setFilterFids(intersecting_ids)) if f.geometry().intersects(line_geom)]
            
            #print(f"Entidades realmente intersectadas: {len(intersecting_features)}")

            if intersecting_features:
                # **Ordenar las parcelas según su posición a lo largo de la línea**
                # Obtener el punto central de cada entidad y calcular su distancia a lo largo de la línea
                parcels_with_distances = []
                for feature in intersecting_features:
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
                    parcels_with_distances.append((feature, min_distance))
                
                # Ordenar las parcelas según la distancia a lo largo de la línea (de menor a mayor)
                parcels_with_distances.sort(key=lambda x: x[1])
                
                # Numerar todas las entidades ordenadas según su posición a lo largo de la línea
                self.layer.startEditing()
                for feature, _ in parcels_with_distances:
                    # Obtener el índice del campo
                    field_index = self.layer.fields().indexOf(self.target_field)
                    
                    # Obtener el valor actual del campo
                    current_value = feature.attribute(field_index) or ''  # Usar una cadena vacía si el valor actual es None

                    if self.concat:
                        # Concatenar el número actual al valor existente
                        new_value = f"{current_value}{self.current_number}"
                    else:
                        # Actualizar el valor del campo con el número actual
                        new_value = f"{self.current_number}"
                    
                    # Establecer el nuevo valor en la entidad
                    feature.setAttribute(field_index, new_value)
                    self.layer.updateFeature(feature)
                    #print(f"Número {self.current_number} aplicado a la parcela con ID {feature.id()}")
                    self.current_number += 1
                
                # Confirmar los cambios
                self.layer.commitChanges()
                
                # Limpiar la selección
                self.layer.removeSelection()
            else:
                print("No se seleccionó ninguna parcela que intersecte con la línea.")
            
            # Resetear los puntos y la goma elástica
            self.points = []
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)

            # Desactivar la herramienta después de terminar
            iface.mapCanvas().unsetMapTool(self)
    
    def activate(self):
        # Al activar la herramienta, inicializar variables
        self.points = []
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setWidth(2)
        self.rubberBand.show()
        print("Por favor, trace una línea y presione Enter para aplicar los números. No inicie la linea dentro de un poligono, hagalo en un punto externo, sino va a causar un error en la numeracion de las dos primeras parcelas.")
        
    def deactivate(self):
        # Al desactivar la herramienta, limpiar la goma elástica y los puntos
        self.points = []
        if self.rubberBand:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        QgsMapTool.deactivate(self)
        print("Numeracion completada.")

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

def NumerarParcelas(numeroInicial=1, campoObjetivo='NOMENCLA', capa=False, concatenar=False):
    """
    Permite numerar poligonos mediante una linea dibujada dinamicamente
    por el usuario.

    PARAMETROS
    numeroInicial: numero entero
        Numero desde el cual iniciara la numeracion.
    campoObjetivo: cadena de caracteres
        Nombre del campo/columna de la tabla donde se va a numerar.
    capa: QgsVectorLayer o cadena de caracteres
        Capa, o nombre de capa, donde se quiere numerar. Por defecto
        toma la capa activa actual
    concatenar: bool
        True o False. Por defecto en Falso, reemplaza el valor previo
        del campo al guardar la numeracion. Si se invoca la funcion con
        conatenar=True, el numero se va a agregar al final del valor
        anterior del campo.

    COMENTARIOS
    Hola, soy un comentario! A veces, cuando ocurre un error, la linea
    dibujada permanece en pantalla. Para quitarla, seleccionar alguna
    otra herramienta de QGis, como Seleccionar Entidades o Editar.

    RETORNO
    Nada
    """


    global numeracion_tool  # Usar la variable global para almacenar la herramienta
    
    if numeroInicial < 0:
        print(f"El número no debe ser negativo.")
        return
    
    # Verificar si se especificó una capa, si no, usar la capa activa
    if not capa:
        capa = iface.activeLayer()
        print(f"No se especificó una capa, operando sobre {capa.name()}.")
    else:
        capa = CheckLayerInMap(capa)
    
    # Verificar si la capa es válida y está en modo edición
    if not capa.isEditable():
        capa.startEditing()
    
    # Comprobar si el campo existe en la capa
    if not campoObjetivo in [field.name() for field in capa.fields()]:
        print(f"! - El campo {campoObjetivo} no existe en la capa.")
        return
    
    # Crear la herramienta de trazado de línea y numeración
    numeracion_tool = LineParcelNumberingTool(iface.mapCanvas(), capa, numeroInicial, campoObjetivo, concatenar)
    
    # Cambiar la herramienta activa a la de trazado de línea y numeración
    iface.mapCanvas().setMapTool(numeracion_tool)

#Gracias por tanto, ChatGPT


def ImprimirDistanciaInterseccion(line_geom):
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

