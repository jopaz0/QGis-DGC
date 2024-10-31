"""
ChamferTool Class Definition (23 Oct 2024) - Jonatan Opazo (j.d.o.dalessandro@gmail.com)
Created for use at DGC with PyQGis, but general enough to implement in other projects.
"""
import math
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from qgis.PyQt.QtCore import Qt
from CommonFunctions import *

class ChamferTool(QgsMapToolEmitPoint):
    """
    Map tool to apply a chamfer cut to a vertex of a polygon in the active layer.

    This tool allows selecting a vertex in a feature of the active layer and creating two new points
    at a specific distance from that vertex. The points are inserted into the polygon's geometry.

    PARAMETERS
    distance: float
        The distance from the vertex to calculate the new points.
    layer: QgsVectorLayer, optional
        The layer on which the tool will be applied. If not provided, the active layer will be used.
    tolerance: float or False
        The tolerance used to simplify repeated points in the geometry. If set to False or similar, no simplification occurs.
    """

    def __init__(self, distance, tolerance=0.01, epsgCode=False):
        """
        Initializes the map tool.

        PARAMETERS
        distance: float
            The distance from the vertex to calculate the new points.
        tolerance: float or False
            The tolerance used to simplify repeated points in the geometry. If set to False or similar, no simplification occurs.
        """
        super().__init__(iface.mapCanvas())
        self.canvas = iface.mapCanvas()
        self.distance = distance
        self.layer = iface.activeLayer()
        self.setCursor(Qt.CrossCursor)
        self.tolerance = tolerance
        self.reproject = True if epsgCode else False
        if epsgCode:
            self.tolerance = 0.0000001
            newCrs = QgsCoordinateReferenceSystem(epsgCode)
            self.newCrs = newCrs
            oldCrs = self.layer.crs()
            self.transformToNewCRS = QgsCoordinateTransform(oldCrs, newCrs, QgsProject.instance())
            self.transformToOldCRS = QgsCoordinateTransform(newCrs, oldCrs, QgsProject.instance())

    def canvasReleaseEvent(self, event):
        """
        Handles the mouse release event on the canvas.

        Upon releasing the mouse button, the tool's logic is called to apply the chamfer cut
        to the selected polygon.

        PARAMETERS
        event: QMouseEvent
            The mouse button release event.
        """
        point = self.toMapCoordinates(event.pos())
        button = event.button()
        self.chamferTool(point, button)

    def chamferTool(self, point, button):
        """
        Cuts a chamfer in the feature lying below the point selected, at the nearest point.

        PARAMETERS
        point: QgsPoint
            The selected point on canvas.
        button: int
            Mouse's released button (usually Qt.LeftButton).
        """
        print('asd')
        if button == Qt.LeftButton:
            rectDist = 0.000001
            rect = QgsRectangle(point.x() - rectDist, point.y() - rectDist, point.x() + rectDist, point.y() + rectDist)
            #Intento de que funcione en Qgis viejos 
            try:
                self.layer.selectByRect(rect, Qgis.SelectBehavior.SetSelection)
            except:
                self.layer.selectByRect(rect, QgsVectorLayer.SetSelection)
            if self.layer.selectedFeatureCount() == 1:
                feature = self.layer.selectedFeatures()[0]
                #this way, if used as standalone tool, it will fail GEOM_DeleteDuplicatePoints and default to the feature geometry
                try:
                    geom = GEOM_DeleteDuplicatePoints(feature.geometry(), self.tolerance) if self.tolerance else feature.geometry()
                except:
                    geom = feature.geometry()
                if self.reproject:
                    geom.transform(self.transformToNewCRS)
                    point = self.transformToNewCRS.transform(point)
                nearestVertex = geom.closestVertex(point)
                vertexIndex = nearestVertex[1]
                vertexPrevIndex = nearestVertex[2]
                vertexNextIndex = nearestVertex[3]
                vertex = geom.vertexAt(vertexIndex)
                vertexPrev = geom.vertexAt(vertexPrevIndex)
                vertexNext = geom.vertexAt(vertexNextIndex)

                angle = math.atan2(vertexPrev.y() - vertex.y(), vertexPrev.x() - vertex.x())
                newX = vertex.x() + self.distance * math.cos(angle)
                newY = vertex.y() + self.distance * math.sin(angle)
                newPointPrev = QgsPoint(newX, newY)

                angle = math.atan2(vertexNext.y() - vertex.y(), vertexNext.x() - vertex.x())
                newX = vertex.x() + self.distance * math.cos(angle)
                newY = vertex.y() + self.distance * math.sin(angle)
                newPointNext = QgsPoint(newX, newY)

                if geom.isMultipart():
                    wktType = 'MultiPolygon '
                    vertices = geom.asMultiPolygon()[0][0]
                else:
                    wktType = 'Polygon '
                    vertices = geom.asPolygon()[0]
                vertices.pop(vertexIndex)
                vertices.insert(vertexIndex, newPointPrev)
                vertices.insert(vertexNextIndex, newPointNext)

                wkt = wktType + ' (((' + ', '.join(f'{p.x()} {p.y()}' for p in vertices) + ')))'
                newGeometry = QgsGeometry.fromWkt(wkt)
                if self.reproject:
                    newGeometry.transform(self.transformToOldCRS)
                if not self.layer.isEditable():
                    self.layer.startEditing()
                self.layer.changeGeometry(feature.id(), newGeometry)
                self.canvas.refresh()
            elif self.layer.selectedFeatureCount() < 1:
                print('No se selecciono una entidad.')
            else:
                print('Se seleccionó más de una entidad. Toca más lejos del borde del polígono!')

    def keyPressEvent(self, event):
        """
        Handles key press events when the tool is active.

        Pressing Esc cancels the use of the tool.

        PARAMETERS
        event: QKeyEvent
            The key press event.
        """
        if event.key() == Qt.Key_Escape:
            self.canvas.setMapTool(QgsMapTool())

    def activate(self):
        """
        Activates the chamfer tool. Displays the mouse a cross.
        """
        self.setCursor(Qt.CrossCursor)
        if self.reproject:
            print(f"Reproyectando geometrias a {self.newCrs.userFriendlyIdentifier()}")

    def deactivate(self):
        """
        Deactivates the chamfer tool.
        """
        self.setCursor(Qt.ArrowCursor)
   
