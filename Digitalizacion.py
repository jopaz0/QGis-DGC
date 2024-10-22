"""
Modulo: Digitalizacion (22 Oct 2024)
Funciones destinadas a digitalizar parcelas.
Funciones: 
    > AsignarValorACampo / nomenclar
    > CortarOchava / ochavar
    > NumerarParcelas / numerar
Tipee help(funcion) en la consola para mas informacion.
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from CommonFunctions import IsValueCompatible
import ChamferTool
import NumberingTool

def AsignarValorACampo(valor, campoObjetivo='NOMENCLA'):
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
    if IsValueCompatible(valor, fieldType):
        with edit(layer):
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

def CortarOchava(distancia=4, capa=None):
    """
    Permite cortar rapidamente ochavas.

    PARAMETROS
    distancia: numero
        Distancia que va a tomar a cada lado del vertice al cortar la ochava.
    capa: QgsVectorLayer
        Capa donde se van a aplicar los cambios. Toma por defecto la capa actual. Mejor no lo toques.

    COMENTARIOS
    Invocar la herramienta permite seleccionar puntos cercanos a un vertice de una geometria. Calcula dos puntos hacia los vertices adyacentes a la distancia especificada (por defecto 4 metros), los inserta y elimina el vertice seleccionado.
    Nada
    """
    tool = ChamferTool(distancia)
    iface.mapCanvas().setMapTool(tool)
cortarochava = CortarOchava
CORTAROCHAVA = CortarOchava
Ochava = CortarOchava
ochava = CortarOchava
OCHAVA = CortarOchava

def NumerarParcelas(numeroInicial=1, campoObjetivo='NOMENCLA', concatenar=True):
    """
    Permite numerar poligonos mediante una linea dibujada dinamicamente por el usuario.

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
    tool = NumberingTool(numeroInicial, campoObjetivo, concatenar)
    iface.mapCanvas().setMapTool(tool)
numerarparcelas = NumerarParcelas
NUMERARPARCELAS = NumerarParcelas
Numerar = NumerarParcelas
numerar = NumerarParcelas
NUMERAR = NumerarParcelas
