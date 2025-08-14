"""
Modulo: Digitalizacion (22 Oct 2024)
Funciones destinadas a digitalizar parcelas.
Funciones: 
 > AsignarValorACampo(valor) / nomenclar(valor) / nomenclar(valor, campo)
- Permite asignar rapidamente un valor en un campo a las parcelas seleccionadas. 
- Por defecto lo asigna en NOMENCLA, pero puede indicarse un campo distinto como segundo parametro.

 > CortarOchava() / ochava() / ochava(5)
- Permite cortar rapidamente ochavas.
- Por defecto toma puntos nuevos a 4 unidades (metros) de distancia hacia los vertices adyacentes al seleccionado, pero puede asignarse otra distancia como primer parametro.
- Por defecto esta configurada para trabajar sobre capas en proyecciones planas. Si se detecta una capa en WGS84, debera asignar un codigo epsg como segundo parametro, para realizar una reproyeccion de la geometria antes de operar.

 > NumerarParcelas() / numerar() / numerar(50, 'PARCELA', False)
- Permite numerar poligonos mediante una linea dibujada dinamicamente por el usuario. 
- Por defecto comienza desde el 1, pero se le puede indicar otro numero inicial como primer parametro.   
- Por defecto opera sobre el campo NOMENCLA, pero se le puede indicar otro campo como segundo parametro.
- Por defecto concatena el numero al valor anterior del campo, pero puede indicarsele que reemplace valores como tercer parametro (usar False o 0).

Tipee help(funcion) en la consola para mas informacion.
#################BARRA SEPARADORA DE BAJO PRESUPUESTO#################
"""
"""
Permite un flujo de trabajo acortado para dibujar las parcelas de los expedientes:
 - Dibujo las parcelas originales, sin las ochavas en caso de que me sea mas siemple (generalmente lo es)
 - Uso OCHAVA() y voy tocando las esquinas donde quiero generarlas. 
   - Si quiero una ochava de mas o menos que 4 metros, uso OCHAVA(#), con # siendo la distancia en metros.
 - Selecciono las parcelas y uso NOMENCLAR('25-1-A-32-') para llenar la parte de la nomenclatura q todas comparten.
   - Si quiero completar otro campo, por ejemplo a PROF ponerle GARCIA, uso NOMENCLAR('GARCIA','PROF')
 - Uso NUMERAR(), lo que me permite trazar una multilinea. La hago cruzando las parcelas en el orden en que se numeran, y presiono Enter.
   - Si la primera parcela de la serie tiene un numero distinto de uno, pongamosle 5, usaria NUMERAR(5)
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from CommonFunctions import *
from ChamferTool import *
from NumberingTool import *

def AsignarValorACampo(valor, campoObjetivo='NOMENCLA'):
    """
    Permite asignar rapidamente un valor en un campo a las entidades seleccionadas.

    PARAMETROS
    valor: numero o cadena de caracteres
        Valor que se va a aplicar.
    campoObjetivo: cadena de caracteres (opcional)
        Nombre del campo/columna de la tabla donde se va a modificar

    COMENTARIOS
    Hola, soy un comentario! Me resulta un poco mas rapido que usar la calculadora de campos, pero es basicamente lo mismo.
    
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
    if not layer.isEditable():
        layer.startEditing()
    if IsValueCompatible(valor, fieldType):
        for feature in features:
            feature[campoObjetivo] = valor
            if not layer.updateFeature(feature):
                print(f"Error al actualizar la entidad.")
                layer.rollBack()
        return True
    else: 
        print(f'El tipo de valor ({fieldType}) proporcionado no era compatible con {campoObjetivo}.')
        return False
asignarvaloracampo = AsignarValorACampo
ASIGNARVALORACAMPO = AsignarValorACampo
Nomenclar = AsignarValorACampo
nomenclar = AsignarValorACampo
NOMENCLAR = AsignarValorACampo
nm = AsignarValorACampo
NM = AsignarValorACampo

def CortarOchava(distancia=4, epsg=False):
    """
    Permite cortar rapidamente ochavas.

    PARAMETROS
    distancia: numero
        Distancia que va a tomar a cada lado del vertice al cortar la ochava.
    epsg: numero
        El codigo EPSG del sistema de coordenadas planas al que reproyectar la geometria antes de cortarla.

    COMENTARIOS
    - Invocar la herramienta permite seleccionar puntos cercanos a un vertice de una geometria. Calcula dos puntos hacia los vertices adyacentes a la distancia especificada (por defecto 4 metros), los inserta y elimina el vertice seleccionado.
    - A veces, al seleccionar un punto, se crean los nuevos vertices pero no se elimina el anterior. Intentar eliminarlo manualmente ANTES de guardar los cambios en la capa, resulta en algunos comportamientos extraños por parte del poligono. No es grave, pero no se como solucionarlo sin forzar un guardado de la capa (no queremos eso, es proferible poder volver atras los cambios)

    RETORNO
    Nada
    """
    epsgCapa = iface.activeLayer().crs()
    epsgProyecto = QgsProject.instance().crs()
    if not epsg and epsgCapa.postgisSrid() == 4326:
        print('El CRS actual del proyecto es WGS84 y no se indico un CRS de reproyeccion.')
        print('Por ejemplo, utilizar ochava(epsg=5346) / ochava(4,5346)')
        print('Faja2=5344, Faja3=5345, Faja4=5346')
        return
    if not epsgCapa.postgisSrid() == epsgProyecto.postgisSrid():
        print('El CRS actual del proyecto y de la capa no coinciden.')
        return
    herramienta = ChamferTool(distancia, epsgCode=epsg)
    iface.mapCanvas().setMapTool(herramienta)
    iface._currentTool = herramienta
cortarochava = CortarOchava
CORTAROCHAVA = CortarOchava
Ochava = CortarOchava
ochava = CortarOchava
OCHAVA = CortarOchava
co = CortarOchava
CO = CortarOchava

def NumerarParcelas(numeroInicial=1, campoObjetivo='NOMENCLA', concatenar=True):
    """
    Permite numerar poligonos mediante una linea dibujada dinamicamente por el usuario.

    PARAMETROS
    numeroInicial: numero entero
        Numero desde el cual iniciara la numeracion.
    campoObjetivo: cadena de caracteres
        Nombre del campo/columna de la tabla donde se va a numerar.
    capa: QgsVectorLayer o cadena de caracteres
        Capa, o nombre de capa, donde se quiere numerar. Por defecto toma la capa activa actual
    concatenar: bool
        True o False. Por defecto en True, indica si la numeracion concatena con el valor previo del campo, o lo reemplaza.

    COMENTARIOS
    Hola, soy un comentario! Esto aplica a TODAS las entidades en la capa actual, no solo a la seleccion.

    RETORNO
    Nada
    """
    herramienta = NumberingTool(numeroInicial, campoObjetivo, concatenar)
    iface.mapCanvas().setMapTool(herramienta)
    iface._currentTool = herramienta
numerarparcelas = NumerarParcelas
NUMERARPARCELAS = NumerarParcelas
Numerar = NumerarParcelas
numerar = NumerarParcelas
NUMERAR = NumerarParcelas
np = NumerarParcelas
NP = NumerarParcelas
