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
    Herramienta para numerar parcelas a lo largo de una línea definida por el usuario en un lienzo de mapa de QGIS.

    Esta herramienta permite al usuario dibujar una línea en el mapa y asignar números secuenciales a las parcelas que 
    intersectan en función de su posición a lo largo de esa línea. La numeración puede reemplazar los valores de atributos 
    existentes o concatenarse a ellos.

    PARAMETROS
    canvas: Referencia al lienzo del mapa de QGIS.
    layer: El objeto QgsVectorLayer que representa la capa que se va a modificar.
    startingNumber: Entero que indica el número de inicio para la numeración de parcelas.
    targetField: Cadena que representa el nombre del campo donde se almacenarán los números.
    concat: Booleano que indica si se debe concatenar la numeración con los valores existentes en el campo objetivo.
    """

    def __init__(self, canvas, layer, startingNumber, targetField, concat):
        """
        Inicializa la herramienta de numeración con el lienzo del mapa, la capa y los parámetros de numeración proporcionados.

        PARAMETROS
        canvas: Referencia al lienzo del mapa de QGIS.
        layer: El objeto QgsVectorLayer que representa la capa que se va a modificar.
        startingNumber: Entero que indica el número de inicio para la numeración de parcelas.
        targetField: Cadena que representa el nombre del campo donde se almacenarán los números.
        concat: Booleano que indica si se debe concatenar la numeración con los valores existentes en el campo objetivo.
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.currentNumber = startingNumber
        self.targetField = targetField
        self.concat = concat
        self.points = []  # Almacena puntos para crear la línea
        self.setCursor(Qt.CrossCursor)  # Cambia el cursor a una cruz cuando se activa la herramienta
        self.rubberBand = None
        print(f"""Herramienta de numeración activada:
 Capa = '{layer.name()}'
 Campo = '{targetField}'
 Número de inicio = {startingNumber},
 Concatenar con datos anteriores = {concat}
""")

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

        Si se presiona la tecla Enter, se crea una geometría de línea a partir de los puntos seleccionados, y se identifican 
        las parcelas que intersectan y se numeran secuencialmente a lo largo de la línea.

        PARAMETROS
        event: Objeto QKeyEvent que representa el evento de la tecla.
        """
        if event.key() == Qt.Key_Return:
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
                self.layer.startEditing()
                for feature, _ in parcelsWithDistances:
                    fieldIndex = self.layer.fields().indexOf(self.targetField)
                    currentValue = feature.attribute(fieldIndex) or ''

                    if self.concat:
                        newValue = f"{currentValue}{self.currentNumber}"
                    else:
                        newValue = f"{self.currentNumber}"

                    feature.setAttribute(fieldIndex, newValue)
                    self.layer.updateFeature(feature)
                    self.currentNumber += 1
                
                self.layer.commitChanges()
                self.layer.removeSelection()
            else:
                print("No se seleccionaron parcelas que intersecten con la línea.")
            
            self.points = []
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
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

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
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

