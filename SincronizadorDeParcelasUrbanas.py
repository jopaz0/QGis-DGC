"""
Modulo: Sincronizador de Parcelas (04 Oct 2024)
Funciones registradas: CompletarPartidas, CompletarTabla
Tipee help(funcion) en la consola para mas informacion.

Este script debe reemplazr al anterior sincronizador, que es una 
reverenda poronga. No deberia trabarse tanto si hay demasiadas
entradas en los CSVs de Progress. Pero no informa de los errores
tan detalladamente como el anterior.
"""

import pandas as pd
import os
import processing
from PyQt5.QtCore import QVariant
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from CommonFunctions import *
from DGCFunctions import *

### BARRA SEPARADORA DE BAJO PRESUPUESTO ###
#Funciones destinadas a uso interno en DGC. O sea, estan en castellano

def SincronizacionUrbana(ejido):
    #Leo, unifico y modifico los XLS/CSV urbanos descargados
    root = r'C:\MaxlocV11'
    csvFiles = [f'Manzana{ejido}.xls',f'Quinta{ejido}.xls',f'Chacra{ejido}.xls']
    enc = 'latin-1'
    separator=';'
    floatFields=['PORCEN','V2','V3','V4']
    fieldNameTranslations={'REGISTRO DE PROP. INMUEBLE':'REGISTRO','NOMENCLATURA':'NOMENCLA','APELLIDO Y NOMBRE':'APELLIDO'}
    fieldsToUppercase=True
    dropFields_aprox=['EXPTE','ANIO']
    dropFields_exact=[]
    outputName = 'MergedCSVs'
    csvPath = CSV_MergeFiles(root, csvFiles, enc, separator, floatFields, fieldNameTranslations, fieldsToUppercase, dropFields_aprox, dropFields_exact, outputName)
    # csv = AddCsvAs(csvPath, outputName)
    
    capas = BuscarCapasUrbanas(ejido)
    # propietarios = AddLayerFromPath(capas['PROPIETARIOS'], 'PROPIETARIOS')
    # poseedores = AddLayerFromPath(capas['POSEEDORES'], 'POSEEDORES')

    

def SincronizarTabla(id):
    if type(id) is int:
        SincronizacionUrbana(id)
    elif type(id) is str:
        print('Esto es solo para ejidos! Ingrese un numero de ejido, no una Seccion o lo que sea.')
        return False
        SincronizacionRural(id)
                            

