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
                                    feature[campo] = feature[f'{prefijo}{campo}']
                                except Exception as e:
                                    #añadir mensaje de error?
                                    continue
                        union.updateFeature(feature)
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
