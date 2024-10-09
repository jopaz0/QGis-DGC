"""
Modulo: Numerador de Parcelas (04 Oct 2024)
Funciones registradas: NumerarParcelas, AsignarValorACampo
Tipee help(funcion) en la consola para mas informacion.
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from qgis.PyQt.QtCore import Qt
from CommonFunctions import CheckLayerInMap, IsCompatible

# Variables para configurar
starting_number = 1  # Número inicial, modificar según sea necesario
target_field = "PARCELA"  # Campo de la entidad donde se almacenará el número
numeracion_tool = None
class LineParcelNumberingTool(QgsMapToolEmitPoint):
    """
    Tool for numbering parcels along a user-defined line in a QGIS map canvas.

    This tool allows the user to draw a line on the map and assign sequential numbers to intersecting parcels 
    based on their position along that line. The numbering can either replace the existing attribute values 
    or be concatenated to them.

    PARAMETERS
    canvas: Reference to the QGIS map canvas.
    layer: The QgsVectorLayer object representing the layer to be modified.
    starting_number: Integer indicating the starting number for the parcel numbering.
    target_field: String representing the field name where the numbers will be stored.
    concat: Boolean indicating whether to concatenate the numbering with existing values in the target field.
    """

    def __init__(self, canvas, layer, starting_number, target_field, concat):
        """
        Initializes the numbering tool with the provided map canvas, layer, and numbering parameters.

        PARAMETERS
        canvas: Reference to the QGIS map canvas.
        layer: The QgsVectorLayer object representing the layer to be modified.
        starting_number: Integer indicating the starting number for the parcel numbering.
        target_field: String representing the field name where the numbers will be stored.
        concat: Boolean indicating whether to concatenate the numbering with existing values in the target field.
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.current_number = starting_number
        self.target_field = target_field
        self.concat = concat
        self.points = []  # Stores points to create the line
        self.setCursor(Qt.CrossCursor)  # Change cursor to crosshair when tool is activated
        self.rubberBand = None
        print(f"""Numbering tool activated:
 Layer = '{layer.name()}'
 Field = '{target_field}'
 Starting number = {starting_number},
 Concatenate with previous data = {concat}
""")

    def canvasPressEvent(self, event):
        """
        Handles the mouse press event on the map canvas.

        Captures the coordinates where the user clicks and adds the point to the line being drawn. 
        Updates the rubber band (visual line) on the canvas to reflect the added points.

        PARAMETERS
        event: QMouseEvent object representing the mouse event.
        """
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        self.points.append(point)
        
        if len(self.points) >= 1:
            self.rubberBand.addPoint(point, True)  # Add points to the rubber band to display the line

    def canvasReleaseEvent(self, event):
        """
        Handles the mouse release event on the map canvas.

        This method is not used in this tool but is required to be defined as part of the QgsMapToolEmitPoint class.

        PARAMETERS
        event: QMouseEvent object representing the mouse event.
        """
        pass

    def keyPressEvent(self, event):
        """
        Handles key press events when the tool is active.

        If the Enter key is pressed, a line geometry is created from the selected points, and intersecting parcels 
        are identified and numbered sequentially along the line.

        PARAMETERS
        event: QKeyEvent object representing the key event.
        """
        if event.key() == Qt.Key_Return:
            if len(self.points) < 2:
                print("At least two points are needed to draw a line.")
                return

            line_geom = QgsGeometry.fromPolylineXY(self.points)

            if self.layer.crs() != self.canvas.mapSettings().destinationCrs():
                line_geom.transform(QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(), self.layer.crs(), QgsProject.instance()))

            spatial_index = QgsSpatialIndex(self.layer.getFeatures())
            intersecting_ids = spatial_index.intersects(line_geom.boundingBox())

            if not intersecting_ids:
                print("No nearby features were found for the drawn line.")
                return

            intersecting_features = [f for f in self.layer.getFeatures(QgsFeatureRequest().setFilterFids(intersecting_ids)) if f.geometry().intersects(line_geom)]

            if intersecting_features:
                # Sort the parcels by their position along the line
                parcels_with_distances = []
                for feature in intersecting_features:
                    distances = []
                    perimeter_line = feature.geometry().convertToType(QgsWkbTypes.LineGeometry, False)
                    intersection_points = perimeter_line.intersection(line_geom)
                    if not intersection_points.isMultipart():
                        min_distance = line_geom.lineLocatePoint(intersection_points)
                    else:
                        for point in intersection_points.asMultiPoint():
                            distance = line_geom.lineLocatePoint(QgsGeometry.fromPointXY(point))
                            distances.append(distance)
                        min_distance = min(distances)
                    parcels_with_distances.append((feature, min_distance))
                
                parcels_with_distances.sort(key=lambda x: x[1])

                # Start editing and apply numbering
                self.layer.startEditing()
                for feature, _ in parcels_with_distances:
                    field_index = self.layer.fields().indexOf(self.target_field)
                    current_value = feature.attribute(field_index) or ''

                    if self.concat:
                        new_value = f"{current_value}{self.current_number}"
                    else:
                        new_value = f"{self.current_number}"

                    feature.setAttribute(field_index, new_value)
                    self.layer.updateFeature(feature)
                    self.current_number += 1
                
                self.layer.commitChanges()
                self.layer.removeSelection()
            else:
                print("No parcels were selected that intersect with the line.")
            
            self.points = []
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
            iface.mapCanvas().unsetMapTool(self)
    
    def activate(self):
        """
        Activates the numbering tool and initializes variables.

        Displays a red rubber band on the map canvas to help visualize the line as it is being drawn.
        """
        self.points = []
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setWidth(2)
        self.rubberBand.show()
        print("Please draw a line and press Enter to apply the numbering. Start the line outside a polygon; otherwise, it may cause numbering errors for the first two parcels.")
        
    def deactivate(self):
        """
        Deactivates the numbering tool, clearing the rubber band and resetting variables.

        This method also completes the numbering process and resets the tool state.
        """
        self.points = []
        if self.rubberBand:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        QgsMapTool.deactivate(self)
        print("Numbering completed.")

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano, al menos los parametros y el docstring
def NumerarParcelas(numeroInicial=1, campoObjetivo='NOMENCLA', capa=False, concatenar=True):
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

def AsignarValorACampo(campoObjetivo, valor):
    """
    Permite asignar rapidamente un valor en un campo a las parcelas
    seleccionadas.

    PARAMETROS
    campoObjetivo: cadena de caracteres
        Nombre del campo/columna de la tabla donde se va a modificar
    valor: numero o cadena de caracteres
        Valor que se va a aplicar.

    COMENTARIOS
    Hola, soy un comentario! Me resulta un poco mas rapido que usar la
    calculadora de campos, pero es basicamente lo mismo. Es potente si 
    combina con NumerarParcelas. Aplica SOLO a entidades seleccionadas
    
    RETORNO
    Nada
    """
    layer = iface.activeLayer()
    features = layer.selectedFeatures()
    if not features:
        print(f'No habia nada seleccionado en {layer.name()}')
        return False
    if not campoObjetivo in [x.name() for x in layer.fields()]:
        print(f'El campo {campoObjetivo} no existe en {layer.name()}')
        return False
    fieldType = layer.fields().field(campoObjetivo).type()
    if IsCompatible(valor, fieldType):
        with edit(layer):
            for feature in features:
                feature[campoObjetivo] = valor
                if not layer.updateFeature(feature):
                        print(f"Error al actualizar la entidad. Esto no deberia ocurrir...")
                        layer.rollBack()
        return True
    else: 
        print(f'El tipo de valor ({fieldType}) proporcionado no era compatible con {campoObjetivo}.')
        return False

