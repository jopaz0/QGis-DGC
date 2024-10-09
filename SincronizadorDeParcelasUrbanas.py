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

def SincronizacionUrbana(ejido):
    #Todos estos son los parametros de entrada para CSV_MergeFiles
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
    
    csvs = CSV_DivideByFieldValue(csvUnido, 'TEN', 'S', enc='latin-1', separator=';')
    csvs = {'PROPIETARIOS': csvs['OTHERS'], 'POSEEDORES': csvs['OTHERS']}
    
    capas = BuscarCapasUrbanas(ejido)
    for ten in ['PROPIETARIOS','POSEEDORES']:
        capa = capas[ten]
        csv = csvs[ten]


    # propietarios = AddLayerFromPath(capas['PROPIETARIOS'], 'PROPIETARIOS')
    # poseedores = AddLayerFromPath(capas['POSEEDORES'], 'POSEEDORES')

    

def SincronizarTabla(id):
    if type(id) is int:
        SincronizacionUrbana(id)
    elif type(id) is str:
        print('Esto es solo para ejidos! Ingrese un numero de ejido, no una Seccion o lo que sea.')
        return False
        SincronizacionRural(id)
                            

