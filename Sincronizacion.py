"""
Modulo: Sincronizacion (25 Oct 2024)
Funciones destinadas a sincronizar las tablas de parcelas (urbanas, de momento) con informacion actualizada. Lee informacion desde los CSV/XLS descargados de Progress.
Funciones:
 > CompletarPartidas(numero de ejido)
- Recupera las partidas de las parcelas seleccionadas, en base a NOMENCLA. 
- Requiere haber descargado los CSV del pueblo en Progress.

 > CompletarTabla(numero de ejido)
- Recupera los valores de todos los campos, en base a PARTIDA.
- Requiere haber descargado los CSV del pueblo en Progress.

 > GenerarEjidoSincronizado(numero de ejido)
- Calcula y carga en el lienzo el resultado de sincronizar todas las parcelas de un ejido. 
- Las parcelas cuya partida no figure en tabla conservan sus datos anteriores, excepto COD, APELLIDO y TEN. 
- No tiene en cuenta parcelas que existan en la tabla pero no en los shapefiles.
- Requiere haber descargado los CSV del pueblo en Progress. 

Seleccionar todo el pueblo y usar COMPLETARPARTIDAS(#) y/o COMPLETARTABLA(#) tecnicamente funciona, pero puede llegar a demorar mucho y corromper los datos de las parcelas que usamos todos.

Tipee help(funcion) en la consola para mas informacion.
#################BARRA SEPARADORA DE BAJO PRESUPUESTO#################
"""
"""
Permite un flujo de trabajo acortado para pasar parcelas de expedientes a registrados. Lo que suelo hacer es:
 (Voy a llamar # al numero del ejido donde se trabaja)
 - Cambiar el mapa al pueblo crrespondiente, usando CAMBIAREJIDO(#)
 - En Progress, descargo las 3 tablas del ejido. Dejo manzanas para lo ultimo y continuo mientras se descarga
 - Selecciono las parcelas de expedientes (ya dibujadas) que hay que registrar
 - Copio las parcelas a la capa de propietarios
 - Con las parcelas seleccionadas y las tablas descargadas, completo las partidas usando COMPLETARPARTIDAS(#)
 - Con las parcelas aun seleccionadas y las partidas completadas, completo el resto de la tabla usando COMPLETARTABLA(#)
"""
from qgis.core import *
from qgis.utils import *
import processing
from qgis.PyQt.QtCore import QVariant
from CommonFunctions import *
from DGCFunctions import *

FUNCIONES = {}
def RegisterFunction(*aliases):
    """
    Decorador para registrar una función y sus alias.
    """
    def wrapper(func):
        FUNCIONES[func.__name__] = {
            "func": func,
            "aliases": list(aliases)
        }
        for alias in aliases:
            globals()[alias] = func
        return func
    return wrapper

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano
@RegisterFunction("completarpartidas", "COMPLETARPARTIDAS", "cp", "CP")
def CompletarPartidas(ejido, capa=False, poseedores=False):
    """
    Completa el campo 'PARTIDA' de las parcelas seleccionadas en la capa actual usando 'NOMENCLA' para comparar con los datos de archivos CSV correspondientes a un ejido especificado.

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
        print(f'No habian parcelas seleccionadas.' )
        return False

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
    for cc in [1, 2, 3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        dic = CSV_ToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)
        if dic:
            if poseedores:
                dic = DICT_Filter(dic, matchFilters={'TEN':'S'})
            else:
                dic = DICT_Filter(dic, unmatchFilters={'TEN':'S'})
            dic = DICT_SetKey(dic, 'NOMENCLA')
            diccionarios[cc] = dic
        else:
            print(f"Archivo CSV no encontrado o vacío: {csvPath}")
            diccionarios[cc] = False
     
    #separo las parcelas por cc y matcheo por nomenclatura con el diccionario que le corresponda
    #de momento, esto no tiene en cuenta PHS
    for cc in [1, 2, 3]:
        if diccionarios[cc]:
            subconjunto = [x for x in entidades if x['CC'] == cc]
            if subconjunto:
                SyncFieldsFromDict(capa, subconjunto, diccionarios[cc], 'NOMENCLA', ['PARTIDA'])

@RegisterFunction("completartabla", "COMPLETARTABLA", "ct", "CT")
def CompletarTabla(ejido, capa = False, sincronizarTodo = False):
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
    
    if not sincronizarTodo:
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
    for cc in [1, 2, 3]:
        csvPath = f'C:\\MaxlocV11\\{nombrecc[cc]}{ejido}.xls'
        csv = CSV_ToDictList(csvPath, floatFields=camposDecimales, dropFields_aprox=camposBorrarAprox, fieldNameTranslations=conversiones)
        if csv:
            diccionario += csv
        else:
            print(f"Archivo CSV no encontrado o vacío: {csvPath}")

    #aplico algunas conversiones a los datos.. parece que solo necesite una
    for entidad in diccionario:
        entidad['MZNA'] = STR_RemoveEndingChars(STR_RemoveStartingChars(entidad['MZNA'], '0'), 'X')

    diccionario = DICT_SetKey(diccionario, 'PARTIDA')

    # Blanqueo los valores de COD, DOCUMENTO, APELLIDO y REGISTRO de las entidades
    if not capa.isEditable():
        capa.startEditing()
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

@RegisterFunction("generarejidosincronizado", "GENERAREJIDOSINCRONIZADO","ges","GES")
def GenerarEjidoSincronizado(ejido):
    """
    Genera capas sincronizadas para el ejido especificado usando PARTIDA como comparacion.
    Requiere las capas de pueblo en el L y los CSV del pueblo descargados desde progress

    PARAMETROS
    ejido: Cadena de texto o numero entero que representa el código del ejido a procesar

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
    plantillas=r'L:\Geodesia\Privado\Opazo\Weas Operativas\Scripts\res\Geodesia'
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
        if not csvUnido:
            print(f'No pude generar el CSV del pueblo.')
            return False
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
                    indices = [union.fields().indexOf(field) for field in camposCSV if union.fields().indexOf(field) != -1]
                    union.dataProvider().deleteAttributes(indices)
                    union.updateFields()
                nombreCapa = f'{ejido}-{ten}-Sincronizado'
                CANVAS_RemoveLayerByName(nombreCapa)
                aux = CANVAS_AddLayer(union, nombreCapa)
                aux2 = f'Sinc-{ten}.qml'
                aux.loadNamedStyle(os.path.join(plantillas,aux2))
                
                #Aca genero el csv (temporal) con las entradas que faltan en la capa de poligonos
                prefijo = 'POL_'
                parametros = {  'DISCARD_NONMATCHING' : False, 
                    'FIELD' : 'PARTIDA', 
                    'FIELDS_TO_COPY' : [], 
                    'FIELD_2' : 'PARTIDA', 
                    'INPUT' : csv, 
                    'INPUT_2' : capa, 
                    'METHOD' : 0, 
                    'OUTPUT' : 'TEMPORARY_OUTPUT', 
                    'PREFIX' : prefijo }
                union = processing.run("native:joinattributestable", parametros)
                union = union['OUTPUT']
                with edit(union):
                    eliminar = []
                    for feature in union.getFeatures():
                        if feature[f'{prefijo}PARTIDA']:
                            eliminar.append(feature.id())
                    union.dataProvider().deleteFeatures(eliminar)
                nombreCapa = f'Faltantes en {ejido}-{ten}'
                CANVAS_AddLayer(union, nombreCapa)
                
            except Exception as e:
                print(f"Error en la sincronización de la capa {ten}. ErrorMSG: {e}")
                continue
            finally:
                CANVAS_RemoveLayer(csv)

    except Exception as e:
        print(f"Error general en la sincronización del ejido {ejido}. ErrorMSG: {e}")






