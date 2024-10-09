"""
Modulo: Sincronizador de Parcelas (04 Oct 2024)
Funciones registradas: CompletarPartidas, CompletarTabla
Tipee help(funcion) en la consola para mas informacion.

Este script debe reemplazr al anterior sincronizador, que es una 
reverenda poronga. No deberia trabarse tanto si hay demasiadas
entradas en los CSVs de Progress. Pero no informa de los errores
tan detalladamente como el anterior.
"""
from CommonFunctions import *
from DGCFunctions import *

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano

def SincronizarEjidoConTablasProgress(ejido):
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
        csvs = {'PROPIETARIOS': csvs['OTHERS'], 'POSEEDORES': csvs['OTHERS']}
        
        capas = BuscarCapasUrbanas(ejido)
        for ten in ['PROPIETARIOS','POSEEDORES']:
            try:
                capa = PathToLayer(capas[ten])
                csv = CANVAS_AddLayer(PathToLayer(csvs[ten], delimiter=';'))
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
                                    feature[campo] = feature[f'{prefijo}{campo}-Sincronizado']
                                except Exception as e:
                                    #añadir mensaje de error?
                                    continue
                        union.updateFeature(feature)
                CANVAS_AddLayer(union, f'{ejido}-{ten}')
            except Exception as e:
                print(f"Error en la sincronización de la capa {ten}. ErrorMSG: {e}")
                continue
            finally:
                CANVAS_RemoveLayer(csv)

    except Exception as e:
        print(f"Error general en la sincronización del ejido {ejido}. ErrorMSG: {e}")