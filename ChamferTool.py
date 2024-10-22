from qgis.core import *
from qgis.utils import *
from qgis.gui import *

class ChamferTool(QgsMapToolEmitPoint):
    """
    Herramienta de mapa para aplicar un corte en ochava a un vértice de un polígono en la capa activa.

    Esta herramienta permite seleccionar un vértice en una entidad de la capa activa y crear dos nuevos puntos
    a una distancia específica desde ese vértice. Los puntos se insertan en la geometría del polígono.

    PARAMETROS
    distance: float
        La distancia desde el vértice para calcular los nuevos puntos.
    layer: QgsVectorLayer, opcional
        La capa en la que se aplicará la herramienta. Si no se proporciona, se utilizará la capa activa.
    """

    def __init__(self, distance):
        """
        Inicializa la herramienta de mapa.

        PARAMETROS
        distance: float
            La distancia desde el vértice para calcular los nuevos puntos.
        layer: QgsVectorLayer, opcional
            La capa en la que se aplicará la herramienta. Si no se proporciona, se utilizará la capa activa.
        """
        canvas = iface.mapCanvas()
        super().__init__(canvas)
        self.canvas = canvas
        self.distance = distance
        self.layer = iface.activeLayer()

    def canvasReleaseEvent(self, event):
        """
        Maneja el evento de liberación del mouse en el canvas.

        Al liberar el botón del mouse, se llama a la lógica de la herramienta para aplicar el corte en ochava
        en el polígono seleccionado.

        PARAMETROS
        event: QMouseEvent
            El evento de liberación del botón del mouse.
        """
        point = self.toMapCoordinates(event.pos())
        button = event.button()
        self.chamferTool(point, button)

    def chamferTool(self, point, button):
        """
        Aplica el corte en ochava al polígono seleccionado en la capa.

        Reemplaza el vértice seleccionado por dos nuevos puntos a la distancia especificada.

        PARAMETROS
        point: QgsPoint
            El punto donde se ha hecho clic en el canvas.
        button: int
            El botón del mouse que se ha liberado (usualmente Qt.LeftButton).
        """
        if button == Qt.LeftButton:
            # Obtener la entidad debajo del punto seleccionado...
            rect = QgsRectangle(point.x() - 0.0001, point.y() - 0.0001, point.x() + 0.0001, point.y() + 0.0001)
            self.layer.selectByRect(rect, Qgis.SelectBehavior.SetSelection)
            if self.layer.selectedFeatureCount() == 1:
                feature = self.layer.selectedFeatures()[0]
                geom = feature.geometry()

                # Obtener el vértice más cercano, el anterior y el siguiente
                nearestVertex = geom.closestVertex(point)
                vertexIndex = nearestVertex[1]
                vertexPrevIndex = nearestVertex[2]
                vertexNextIndex = nearestVertex[3]
                vertex = geom.vertexAt(vertexIndex)
                vertexPrev = geom.vertexAt(vertexPrevIndex)
                vertexNext = geom.vertexAt(vertexNextIndex)

                # Calcular los dos puntos a 'distancia' del vértice
                angle = math.atan2(vertexPrev.y() - vertex.y(), vertexPrev.x() - vertex.x())
                newX = vertex.x() + self.distance * math.cos(angle)
                newY = vertex.y() + self.distance * math.sin(angle)
                newPointPrev = QgsPoint(newX, newY)

                angle = math.atan2(vertexNext.y() - vertex.y(), vertexNext.x() - vertex.x())
                newX = vertex.x() + self.distance * math.cos(angle)
                newY = vertex.y() + self.distance * math.sin(angle)
                newPointNext = QgsPoint(newX, newY)

                # Reemplazar el vértice con los nuevos puntos
                if geom.isMultipart():
                    wktType = 'MultiPolygon '
                    vertices = geom.asMultiPolygon()[0][0]
                else:
                    wktType = 'Polygon '
                    vertices = geom.asPolygon()[0]
                vertices[vertexIndex] = newPointPrev
                vertices.insert(vertexNextIndex, newPointNext)

                # Actualizar la geometría
                wkt = wktType + ' (((' + ', '.join(f'{p.x()} {p.y()}' for p in vertices) + ')))'
                newGeometry = QgsGeometry.fromWkt(wkt)
                if not self.layer.isEditable():
                    self.layer.startEditing()
                self.layer.changeGeometry(feature.id(), newGeometry)
                self.canvas.refresh()
            else:
                print('Se seleccionó más de una entidad. Toca más lejos del borde del polígono!')

    def keyPressEvent(self, event):
        """
        Maneja los eventos de pulsación de teclas cuando la herramienta está activa.

        Al presionar Esc, cancela el uso de la herramienta.

        PARAMETROS
        event: QKeyEvent
            El evento de pulsación de tecla.
        """
        if event.key() == Qt.Key_Escape:
            self.canvas.setMapTool(QgsMapTool())
   