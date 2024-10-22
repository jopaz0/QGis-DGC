from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from qgis.PyQt.QtCore import Qt
from PyQt5.QtCore import QVariant

class NumberingTool(QgsMapToolEmitPoint):
    """
    Herramienta para numerar parcelas a lo largo de una línea definida por el usuario en un lienzo de mapa de QGIS.

    Esta herramienta permite al usuario dibujar una línea en el mapa y asignar números secuenciales a las parcelas que 
    intersectan en función de su posición a lo largo de esa línea. La numeración puede reemplazar los valores de atributos 
    existentes o concatenarse a ellos.

    PARAMETROS
    startingNumber: Entero que indica el número de inicio para la numeración de parcelas.
    targetField: Cadena que representa el nombre del campo donde se almacenarán los números.
    concat: Booleano que indica si se debe concatenar la numeración con los valores existentes en el campo objetivo.
    """

    def __init__(self, startingNumber=1, targetField='NOMENCLA', concat=True):
        """
        Inicializa la herramienta de numeración con el lienzo del mapa, la capa y los parámetros de numeración proporcionados.

        PARAMETROS
        startingNumber: Entero que indica el número de inicio para la numeración de parcelas.
        targetField: Cadena que representa el nombre del campo donde se almacenarán los números.
        concat: Booleano que indica si se debe concatenar la numeración con los valores existentes en el campo objetivo. Si el campo proporcionado es numerico, se reemplaza el valor directamente.
        """
        canvas = iface.mapCanvas()
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = iface.activeLayer()

        if startingNumber < 0:
            print(f"El número no debe ser negativo.")
            canvas.unsetMapTool(self)
        else:
            self.currentNumber = startingNumber

        if not targetField in [field.name() for field in iface.activeLayer().fields()]:
            print(f"! - El campo {targetField} no existe en la capa.")
            canvas.unsetMapTool(self)
        else:
            self.targetField = targetField

        #aca habria que agregar una comprobacion, que sea siempre False si el el tipo de dato de targetField no es string.
        self.concat = concat
        
        self.points = []  # Almacena puntos para crear la línea
        self.setCursor(Qt.CrossCursor)  # Cambia el cursor a una cruz cuando se activa la herramienta
        self.rubberBand = None
        print(f'Herramienta de numeración activada:')
        print(f'Capa = {iface.activeLayer().name()}')
        print(f'Campo = {targetField}')
        print(f'Número de inicio = {startingNumber}')
        print(f'Concatenar con datos anteriores = {concat}')

    def canvasPressEvent(self, event):
        """
        Maneja el evento de pulsación del mouse en el lienzo del mapa.

        Captura las coordenadas donde el usuario hace clic y agrega el punto a la línea que se está dibujando. 
        Actualiza el rubber band (línea visual) en el lienzo para reflejar los puntos agregados.

        PARAMETROS
        event: Objeto QMouseEvent que representa el evento del mouse.
        """
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        self.points.append(point)
        
        if len(self.points) >= 1:
            self.rubberBand.addPoint(point, True)  # Agrega puntos al rubber band para mostrar la línea

    def canvasReleaseEvent(self, event):
        """
        Maneja el evento de liberación del mouse en el lienzo del mapa.

        Este método no se utiliza en esta herramienta pero debe definirse como parte de la clase QgsMapToolEmitPoint.

        PARAMETROS
        event: Objeto QMouseEvent que representa el evento del mouse.
        """
        pass

    def keyPressEvent(self, event):
        """
        Maneja los eventos de pulsación de teclas cuando la herramienta está activa.

        Si se presiona la tecla Enter, se crea una geometría de línea a partir de los puntos seleccionados, y se identifican las parcelas que intersectan y se numeran secuencialmente a lo largo de la línea.
        Al presionar Esc, cancela el uso de la herramienta.

        PARAMETROS
        event: Objeto QKeyEvent que representa el evento de la tecla.
        """
        if event.key() == Qt.Key_Return:
            if not self.layer.isEditable():
                self.layer.startEditing()
            if len(self.points) < 2:
                print("Se necesitan al menos dos puntos para dibujar una línea.")
                return

            lineGeom = QgsGeometry.fromPolylineXY(self.points)

            if self.layer.crs() != self.canvas.mapSettings().destinationCrs():
                lineGeom.transform(QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(), self.layer.crs(), QgsProject.instance()))

            spatialIndex = QgsSpatialIndex(self.layer.getFeatures())
            intersectingIds = spatialIndex.intersects(lineGeom.boundingBox())

            if not intersectingIds:
                print("No se encontraron características cercanas para la línea dibujada.")
                return

            intersectingFeatures = [f for f in self.layer.getFeatures(QgsFeatureRequest().setFilterFids(intersectingIds)) if f.geometry().intersects(lineGeom)]

            if intersectingFeatures:
                # Ordena las parcelas por su posición a lo largo de la línea
                parcelsWithDistances = []
                for feature in intersectingFeatures:
                    distances = []
                    perimeterLine = feature.geometry().convertToType(QgsWkbTypes.LineGeometry, False)
                    intersectionPoints = perimeterLine.intersection(lineGeom)
                    if not intersectionPoints.isMultipart():
                        minDistance = lineGeom.lineLocatePoint(intersectionPoints)
                    else:
                        for point in intersectionPoints.asMultiPoint():
                            distance = lineGeom.lineLocatePoint(QgsGeometry.fromPointXY(point))
                            distances.append(distance)
                        minDistance = min(distances)
                    parcelsWithDistances.append((feature, minDistance))
                
                parcelsWithDistances.sort(key=lambda x: x[1])

                # Comienza a editar y aplicar la numeración
                for feature, _ in parcelsWithDistances:
                    fieldIndex = self.layer.fields().indexOf(self.targetField)
                    fieldType = self.layer.fields()[fieldIndex].type()
                    currentValue = feature.attribute(fieldIndex) or ''
                    if fieldType == QVariant.Int:
                        # Si el tipo de campo es entero, solo asignar el número actual
                        newValue = self.currentNumber
                    else:
                        # Para otros tipos (por ejemplo, texto), asignar el valor concatenado
                        if self.concat:
                            newValue = f"{currentValue}{self.currentNumber}"
                        else:
                            newValue = f"{self.currentNumber}"
                    feature.setAttribute(fieldIndex, newValue)
                    self.layer.updateFeature(feature)
                    self.currentNumber += 1
                
                #self.layer.commitChanges()
                self.layer.removeSelection()
            else:
                print("No se seleccionaron parcelas que intersecten con la línea.")
            
            self.points = []
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
            iface.mapCanvas().unsetMapTool(self)
        elif event.key() == Qt.Key_Escape:
            iface.mapCanvas().unsetMapTool(self)
    
    def activate(self):
        """
        Activa la herramienta de numeración e inicializa las variables.

        Muestra un rubber band rojo en el lienzo del mapa para ayudar a visualizar la línea mientras se está dibujando.
        """
        self.points = []
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setWidth(2)
        self.rubberBand.show()
        print("Por favor dibuje una línea y presione Enter para aplicar la numeración. Comience la línea fuera de un polígono; de lo contrario, puede causar errores de numeración para las dos primeras parcelas.")
        
    def deactivate(self):
        """
        Desactiva la herramienta de numeración, limpiando el rubber band y restableciendo variables.

        Este método también completa el proceso de numeración y restablece el estado de la herramienta.
        """
        self.points = []
        if self.rubberBand:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        QgsMapTool.deactivate(self)
        print("Numeración completada.")
