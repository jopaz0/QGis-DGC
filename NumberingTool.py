"""
NumberingTool Class Definition (23 Oct 2024) - Jonatan Opazo (j.d.o.dalessandro@gmail.com)
Created for use at DGC with PyQGis, but general enough to implement in other projects.
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from qgis.PyQt.QtCore import Qt
from PyQt5.QtCore import QVariant

class NumberingTool(QgsMapToolEmitPoint):
    """
    Tool to number parcels along a user-defined line on a QGIS map canvas.

    This tool allows the user to draw a line on the map and assign sequential numbers to the parcels 
    intersecting based on their position along that line. The numbering can either replace existing 
    attribute values or be concatenated to them.

    PARAMETERS
    startingNumber: Integer indicating the starting number for parcel numbering.
    targetField: String representing the name of the field where the numbers will be stored.
    concat: Boolean indicating whether to concatenate the numbering with the existing values in the target field.
    """

    def __init__(self, startingNumber=1, targetField='NOMENCLA', concat=True):
        """
        Initializes the numbering tool with the map canvas, layer, and the provided numbering parameters.

        PARAMETERS
        startingNumber: Integer indicating the starting number for parcel numbering.
        targetField: String representing the name of the field where the numbers will be stored.
        concat: Boolean indicating whether to concatenate the numbering with existing values in the target field.
                If the provided field is numeric, the value is directly replaced.
        """
        canvas = iface.mapCanvas()
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = iface.activeLayer()

        if startingNumber < 0:
            print(f"Number must be positive or zero.")
            canvas.unsetMapTool(self)
        else:
            self.currentNumber = startingNumber

        if not targetField in [field.name() for field in iface.activeLayer().fields()]:
            print(f"! - Field {targetField} did not exists in the layer.")
            canvas.unsetMapTool(self)
        else:
            self.targetField = targetField

        #aca habria que agregar una comprobacion, que sea siempre False si el el tipo de dato de targetField no es string.
        self.concat = concat
        
        self.points = []  # Almacena puntos para crear la línea
        self.setCursor(Qt.CrossCursor)  # Cambia el cursor a una cruz cuando se activa la herramienta
        self.rubberBand = None
        print(f'Numbring Tool Activated:')
        print(f'Layer = {iface.activeLayer().name()}')
        print(f'Field = {targetField}')
        print(f'Starting Number = {startingNumber}')
        print(f'Concatenate = {concat}')

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
            self.rubberBand.addPoint(point, True)  # Agrega puntos al rubber band para mostrar la línea

    def canvasReleaseEvent(self, event):
        """
        Handles the mouse release event on the map canvas.

        This method is not used in this tool but must be defined as part of the QgsMapToolEmitPoint class.

        PARAMETERS
        event: QMouseEvent object representing the mouse event.
        """
        pass

    def keyPressEvent(self, event):
            """
            Handles key press events when the tool is active.

            If the Enter key is pressed, it creates a line geometry from the selected points and identifies the parcels 
            that intersect with it, numbering them sequentially along the line.
            Pressing Esc cancels the use of the tool.

            PARAMETERS
            event: QKeyEvent object representing the key press event.
            """
            if event.key() == Qt.Key_Return:
                
                if len(self.points) < 2:
                    print("At least two points are needed to draw a line.")
                    return

                lineGeom = QgsGeometry.fromPolylineXY(self.points)

                if self.layer.crs() != self.canvas.mapSettings().destinationCrs():
                    lineGeom.transform(QgsCoordinateTransform(self.canvas.mapSettings().destinationCrs(), self.layer.crs(), QgsProject.instance()))

                spatialIndex = QgsSpatialIndex(self.layer.getFeatures())
                intersectingIds = spatialIndex.intersects(lineGeom.boundingBox())

                if not intersectingIds:
                    print("No nearby features found for the drawn line.")
                    return

                intersectingFeatures = [f for f in self.layer.getFeatures(QgsFeatureRequest().setFilterFids(intersectingIds)) if f.geometry().intersects(lineGeom)]

                if intersectingFeatures:
                    # Sort parcels by their position along the line
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

                    # Begin editing and applying the numbering
                    for feature, _ in parcelsWithDistances:
                        fieldIndex = self.layer.fields().indexOf(self.targetField)
                        fieldType = self.layer.fields()[fieldIndex].type()
                        currentValue = feature.attribute(fieldIndex) or ''
                        if fieldType == QVariant.Int:
                            # If the field type is integer, just assign the current number
                            newValue = self.currentNumber
                        else:
                            # For other types (e.g., text), assign the concatenated value
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
                    print("No parcels intersecting the line were selected.")
                
                self.points = []
                self.rubberBand.reset(QgsWkbTypes.LineGeometry)
                iface.mapCanvas().unsetMapTool(self)
            elif event.key() == Qt.Key_Escape:
                iface.mapCanvas().unsetMapTool(self)
    
    def activate(self):
        """
        Activates the numbering tool and initializes variables.

        Displays a red rubber band on the map canvas to help visualize the line being drawn.
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

        This method also completes the numbering process and resets the tool's state.
        """
        self.points = []
        if self.rubberBand:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        QgsMapTool.deactivate(self)
        print("Numbering Completed")
