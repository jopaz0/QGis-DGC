"""
Modulo: Sincronizador de Parcelas (10 Oct 2024)
Funciones registradas: GenerarEjidoSincronizado
Tipee help(funcion) en la consola para mas informacion.

Este script debe reemplazr al anterior sincronizador, que es una 
reverenda poronga. No deberia trabarse tanto si hay demasiadas
entradas en los CSVs de Progress. Pero no informa de los errores
tan detalladamente como el anterior.
"""
from qgis.core import *
from qgis.utils import *
import processing
from qgis.PyQt.QtCore import QVariant
from CommonFunctions import *
from DGCFunctions import *

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano
def CompletarPartidas(ejido, capa=False, poseedores=False):
    """
    Completa el campo 'PARTIDA' en la capa especificada basado en datos de archivos CSV correspondientes a un ejido especificado.

    PARÁMETROS
    ejido: Entero o cadena que representa el código del ejido a procesar.
    capa: Objeto QgsVectorLayer que representa la capa vectorial a actualizar. Si no se especifica, se utilizará la capa activa en el lienzo de QGIS.
    poseedores: Booleano que indica si se deben filtrar los registros para poseedores (True) o propietarios (False). El valor por defecto es False.
    soloSeleccionados: Booleano que indica si solo se procesarán las entidades seleccionadas (True) o todas las entidades en la capa (False). El valor por defecto es True.

    COMENTARIOS
    - La funcion no diferencia parcelas de propietarios normales de parcelas de propiedad horizontal. Las parcelas con CC = 4 o 5 no se sincronizaran.
    - La función verifica la presencia de campos requeridos ('NOMENCLA', 'PARTIDA', 'CC', 'TEN') en la capa. Si falta alguno, se imprime un mensaje de error y la función finaliza.
    - Se obtienen diccionarios de datos de archivos CSV ubicados en la carpeta `C:\MaxlocV11`. Los CSV relevantes se filtran según el campo 'TEN' de acuerdo con el parámetro `poseedores`.
    - Las parcelas se separan por 'CC' y el campo 'PARTIDA' se actualiza utilizando un método de sincronización basado en el campo 'NOMENCLA'.

    RETORNO
    No retorna ningún valor.
    """
    if capa:
        capa = CANVAS_CheckForLayer(capa)
    else:
        capa = iface.activeLayer()

    entidades = CANVAS_CheckSelection(capa)
    if not entidades:
        return

    #controlo que existan los campos que necesito en la capa. asumo que los que vienen de csv estan bien
    for campo in ['NOMENCLA','PARTIDA', 'CC','TEN']:
        if not campo in [x.name() for x in capa.fields()]:
            print(f'La capa {capa.name()} no tenia el campo {campo}' )
            return False

    #obtengo los diccionarios desde disco
    diccionarios = {1:False,2:False,3:False}
    nombrecc = {1:'Chacra',2:'Quinta',3:'Manzana'}
    camposDecimales = ['PORCEN','V2','V3','V4']
    camposBorrarAprox = ['EXPTE','ANIO']
    conversiones = {'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    for cc in [1,2,3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        diccionarios[cc] = CSV_ToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)
        if poseedores:
            diccionarios[cc] = DICT_Filter(diccionarios[cc], matchFilters={'TEN':'S'})
        else:
            diccionarios[cc] = DICT_Filter(diccionarios[cc], unmatchFilters={'TEN':'S'})

        diccionarios[cc] = DICT_SetKey(diccionarios[cc], 'NOMENCLA')

    #separo las parcelas por cc y matcheo por nomenclatura con el diccionario que le corresponda
    #de momento, esto no tiene en cuenta PHS
    for cc in [1,2,3]:
        subconjunto = [x for x in entidades if x['CC']==cc]
        SyncFieldsFromDict(capa, subconjunto, diccionarios[cc], 'NOMENCLA', ['PARTIDA'])
completarpartidas = CompletarPartidas
COMPLETARPARTIDAS = CompletarPartidas

def CompletarTabla(ejido, capa = False):
    """
    Completa los valores de atributos de las parcelas seleccionadas en la capa actual, basándose en la información obtenida de archivos CSV correspondientes a un ejido.

    PARÁMETROS
    ejido: Número entero o cadena de texto que representa el código del ejido a procesar. 
    capa: Capa vectorial de tipo QgsVectorLayer en la que se van a actualizar los datos. Si no se especifica, se tomará la capa activa en el lienzo de QGIS.
    soloSeleccionados: Booleano que indica si solo se procesarán las entidades seleccionadas (True) o todas las entidades de la capa (False). Por defecto es True.

    COMENTARIOS
    - Se espera que la capa contenga los campos 'PARTIDA' y 'CC'. Si alguno de estos campos no se encuentra en la capa, la función devolverá un mensaje de error y finalizará.
    - Los datos de los archivos CSV se cargan desde la carpeta `C:\MaxlocV11` y se unifican en una lista de diccionarios. Se aplican ciertas conversiones a los campos, como eliminar caracteres iniciales y finales en los nombres de manzana ('MZNA').
    - Los campos 'COD', 'DOCUMENTO', 'APELLIDO' y 'REGISTRO' de la capa se blanquean antes de realizar la sincronización con el diccionario.
    - Si la clave 'PARTIDA' de una entidad no se encuentra en el diccionario, se mantendrán los valores en blanco en los campos especificados.

    RETORNO
    No retorna ningún valor.

    EXCEPCIONES
    - Si la capa especificada no contiene los campos requeridos ('PARTIDA', 'CC'), se imprime un mensaje de error y la función se interrumpe.
    - Si la selección de entidades está vacía o la capa no tiene ninguna entidad, se imprime un mensaje y la función se interrumpe.
    - Captura y maneja cualquier error durante la edición de la capa, imprimiendo mensajes de error y revirtiendo los cambios si es necesario.

    """
    #controlo el input de la capa y seleccion
    if capa:
        capa = CANVAS_CheckForLayer(capa)
    else:
        capa = iface.activeLayer()

    seleccion = CANVAS_CheckSelection(capa)
    if not seleccion:
        return

    #controlo que existan los campos que necesito en la capa. asumo que los que vienen de csv estan bien
    for campo in ['PARTIDA', 'CC']:
        if not campo in [x.name() for x in capa.fields()]:
            print(f'La capa {capa.name()} no tenia el campo {campo}' )
            return False

    #obtengo las listas de diccionarios desde disco y los unifico
    diccionario = []
    nombrecc = {1:'Chacra',2:'Quinta',3:'Manzana'}
    camposDecimales = ['PORCEN','V2','V3','V4']
    camposBorrarAprox = ['EXPTE','ANIO']
    conversiones = {'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    for cc in [1,2,3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        diccionario += CSV_ToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)

    #aplico algunas conversiones a los datos.. parece que solo necesite una
    for entidad in diccionario:
        entidad['MZNA'] = RemoveEndingChars(RemoveStartingChars(entidad['MZNA'], '0'), 'X')

    diccionario = DICT_SetKey(diccionario, 'PARTIDA')

    # Blanqueo los valores de COD, DOCUMENTO, APELLIDO y REGISTRO de las entidades
    with edit(capa):
        for entidad in seleccion:
            for campo in ['COD','DOCUMENTO','APELLIDO','REGISTRO']:
                if not campo in [x.name() for x in capa.fields()]:
                    print(f'La capa {capa.name()} no tenia el campo {campo}' )
                else:
                    entidad[campo] = None
            if not capa.updateFeature(entidad):
                print(f"Error al blanquear la capa. Revertiendo cambios.")
                capa.rollBack()
    # Si no se encuentra la partida en el diccionario, es xq no existen
    SyncFieldsFromDict(capa, seleccion, diccionario, 'PARTIDA')
completartabla = CompletarTabla
COMPLETARTABLA = CompletarTabla

def GenerarEjidoSincronizado(ejido):
    """
    Genera capas sincronizadas para el ejido especificado combinando la geometria de los shapefiles y la información de archivos CSV descargados de Progress. 

    PARAMETROS
    ejido: Cadena de texto o numero entero que representa el código del ejido a procesar. Se ajustará para tener un formato de tres caracteres usando ceros a la izquierda si es necesario.

    COMENTARIOS
    - Se presupone que los CSV estan ya descargados desde la app CatastroV11 y guardados en C:\MaxlocV11\, o sea la ubicacion por defecto. La funcion se encarga de normalizar los datos y encabezados que vienen por defecto.
    - Se presupone que las capas de origen estan ubicadas en la ubicacion por defecto en PUEBLOS CAD-GIS, poseen los campos normalizados y el campo PARTIDA ya completado. Las capas originales no sufren cambios.
    - La funcion genera capas temporales, sincroniza los datos segun PARTIDA y las carga al lienzo de QGIS.
    - Las parcelas cuya partida no tuviera su contraparte en los CSV, mantendran sus datos originales, excepto COD, DOCUMENTO y APELLIDO, que quedaran en blanco.

    RETORNO
    No retorna ningún valor.

    EXCEPCIONES
    - Captura errores relacionados con la carga de capas, manejo de archivos y operaciones de unión de tablas.
    - Cualquier excepción se imprime en la consola para diagnóstico.
    
    """
    #Todos estos son los parametros de entrada para CSV_MergeFiles
    try:
        directoriosCSVs = r'C:\MaxlocV11'
        listaCsvs = [f'Manzana{ejido}.xls',f'Quinta{ejido}.xls',f'Chacra{ejido}.xls']
        codificacionCsv = 'latin-1'
        separador=';'
        camposNumericosDecimales=['PORCEN','V2','V3','V4']
        sustitucionesDeEncabezados={'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
        encabezadosAMayusculas=True
        eliminarColumnasParecidas=['EXPTE','ANIO']
        eliminarColumnas=[]
        nombreCsvUnido = 'MergedCSVs'
        csvUnido = CSV_MergeFiles(directoriosCSVs, listaCsvs, codificacionCsv, separador, camposNumericosDecimales, sustitucionesDeEncabezados, encabezadosAMayusculas, eliminarColumnasParecidas, eliminarColumnas, nombreCsvUnido)
        
        ejido = STR_FillWithChars(ejido, 3, '0')
        csvs = CSV_DivideByFieldValue(csvUnido, 'TEN', 'S', enc='latin-1', separator=';')
        csvs = {'PROPIETARIOS': csvs['OTHERS'], 'POSEEDORES': csvs['MATCH']}
        
        capas = BuscarCapasUrbanas(ejido)
        for ten in ['PROPIETARIOS','POSEEDORES']:
            try:
                capa = PathToLayer(capas[ten])
                csv = CANVAS_AddLayer(PathToLayer(csvs[ten], delimiter=';'))
                nCapa = capa.featureCount()
                nCsv = csv.featureCount()
                print(f'Cantidad de entidades en {capa.name()} ({nCapa}) vs csv ({nCsv})')
                prefijo = 'CSV_'
                parametros = { 'DISCARD_NONMATCHING' : False, 
                            'FIELD' : 'PARTIDA', 
                            'FIELDS_TO_COPY' : [], 
                            'FIELD_2' : 'PARTIDA', 
                            'INPUT' : capa, 
                            'INPUT_2' : csv, 
                            'METHOD' : 0, 
                            'OUTPUT' : 'TEMPORARY_OUTPUT', 
                            'PREFIX' : prefijo }
                union = processing.run("native:joinattributestable", parametros)
                if union['UNJOINABLE_COUNT'] > 0:
                    n = union['UNJOINABLE_COUNT']
                    print(f'Advertencia, {n} parcelas de {ten} no pudieron unirse a la tabla.')
                union = union['OUTPUT']

                #obtengo todos los campos del shape, excepto el de PARTIDA que uso como ID
                campos = [f.name() for f in capa.fields() if f.name() != 'PARTIDA']

                #Columnas a blanquear. Si la partida no existe en la tabla, es xq se dio de baja, y quedan en blanco
                camposEnBlanco = ['COD','DOCUMENTO','APELLIDO']

                with edit(union):
                    for feature in union.getFeatures():
                        if not feature[f'{prefijo}PARTIDA']:
                            for campo in camposEnBlanco:
                                feature[campo] = None  # Establecer el valor en nulo
                        else:
                            for campo in campos:
                                try:
                                    if campo == 'MZNA':
                                        feature[campo] = STR_RemoveEndingChars(STR_RemoveStartingChars(feature[f'{prefijo}{campo}']    ,'0'),'X')
                                    else:
                                        feature[campo] = feature[f'{prefijo}{campo}']
                                except Exception as e:
                                    #añadir mensaje de error?
                                    continue
                        union.updateFeature(feature)
                    camposCSV = [f.name() for f in union.fields() if f.name().startswith(prefijo)]
                    union.removeFields(camposCSV)
                nombreCapa = f'{ejido}-{ten}-Sincronizado'
                CANVAS_RemoveLayerByName(nombreCapa)
                CANVAS_AddLayer(union, nombreCapa)
            except Exception as e:
                print(f"Error en la sincronización de la capa {ten}. ErrorMSG: {e}")
                continue
            finally:
                CANVAS_RemoveLayer(csv)

    except Exception as e:
        print(f"Error general en la sincronización del ejido {ejido}. ErrorMSG: {e}")
generarejidosincronizado = GenerarEjidoSincronizado
GENERAREJIDOSINCRONIZADO = GenerarEjidoSincronizado


