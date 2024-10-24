"""
Modulo: Ayudas (23 Oct 2024)
Funciones varias para agilizar o automatizar el trabajo diario en DGC.
Funciones: 
 > Abrir
 > Backup
 > BackupLigero
 > CambiarEjido
 > InfoEjido / info
 > ActualizarShapesPueblo / rehacermzsyregs
 > GenerarShapeManzanas / rehacermzs
 > GenerarShapeRegistrados / rehacerregs
 > RecargarInfoEjidos
Tipee help(funcion) en la consola para mas informacion.

Fomentando la vagancia responsable desde 2017!
"""
import os, zipfile
from pathlib import Path
from qgis.core import *
from CommonFunctions import *
from DGCFunctions import *

def Abrir(regs):
    """
    Abre los registrados solicitados.

    PARAMETROS
    regs: numero o cadena de caracteres
        En caso de recibir un numero abre solo un registrado. Si recibe una cadena de numeros separados por espacios, comas o guiones, abre una serie de registrados todos a la vez.
    
    COMENTARIOS
    - La función busca en el directorio L:\Geodesia\Privado\Registrados.

    RETORNO
    Nada
    """
    directory  = r'L:\Geodesia\Privado\Registrados'
    if not os.path.exists(directory):
        directory  = r'C:\Geodesia\Privado\Registrados'
    if type(regs) is int:
        regs = [str(regs)]
    elif type(regs) is str:
        regs = regs.rstrip().lstrip().replace('.','').replace(',',' ').replace('-',' ').split(' ')
        regs = [reg for reg in regs if reg != '']
    regs = [STR_FillWithChars(reg,5,'0') for reg in regs]
    for reg in regs:
        try:
            path = os.path.join(directory, f'{reg[0:2]}.000', f'{reg[0:2]}.{reg[2]}00')
            if os.path.exists(path):
                for file in os.listdir(path):
                    if f'{reg[0:2]}.{reg[2:]}' in file and file.endswith('.pdf'):
                        os.startfile(os.path.join(path, file))
        except Exception as e:
            print(f'Error al abrir el registrado {reg}. ErrorMSG: {e}')
abrir = Abrir
ABRIR = Abrir

def ActualizarShapesPueblo(ejido, distanciaBuffer=0.05, agregarAlLienzo=True, sustituirCapas=True):
    """
    Genera los shapes de Manzanas y Registrados de un ejido a partir de sus parcelas.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        El numero del ejido a regenerar
    sustituirCapas: booleano
        Opcional, por defecto Verdadero, sustituye las capas previas en PLANO PUEBLO del ejido
    agregarAlLienzo: booleano
        Opcional, por defecto Verdadero, carga las capas generadas al lienzo de QGis
    
    COMENTARIOS
    - La función transforma automaticamente el numero de ejido a una cadena de 3 digitos completando con ceros.
    - Si sustituirCapas es verdadero, elimina las capas de manzanas y registrados anteriores, de forma irreversible

    RETORNO
    """
    manzanas = GenerarShapeManzanas(ejido, distanciaBuffer, agregarAlLienzo)
    registrados = GenerarShapeRegistrados(ejido, distanciaBuffer, agregarAlLienzo)
    if not sustituirCapas:
        return
    capas = BuscarCapasUrbanas(ejido)
    carpeta = os.path.dirname(capas['MANZANAS'])
    capasViejas = [os.path.join(carpeta, archivo) for archivo in os.listdir(carpeta) if 'MANZANA' in archivo.upper() or 'REGISTRADO' in archivo.upper()]
    for capa in capasViejas:
        try:
            os.remove(capa)
        except Exception as e:
            print(f'No pude eliminar {capa}. ErrorMSG: {e}')
    for capa in [manzanas, registrados]:
        try:
            QgsVectorFileWriter.writeAsVectorFormat(capa, os.path.join(carpeta, f'{capa.name()}.shp'), 'utf-8', driverName='ESRI Shapefile')
        except:
            print(f'No pude guardar la capa {capa.name()}. ErrorMSG: {e}')
RehacerMzsYRegs = ActualizarShapesPueblo
rehacermzsyregs = ActualizarShapesPueblo
REHACERMZSYREGS = ActualizarShapesPueblo

def CambiarEjido (ejido, circ=False, radio=False, cc=False, mzna=False):
    """
    Cambia las capas del mapa de trabajo predeterminado al pueblo indicado y lo enfoca. 

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        El numero del ejido a mostrar
    circ: numero entero
        Opcional, la circunscripcion a filtrar
    radio: caracter
        Opcional, el radio a filtrar. No es sensible a mayusculas
    cc: numero entero
        Opcional, el cc a filtrar 
    mzna: numero entero o cadena de caracteres
        Opcional, la mzna a filtrar. No es sensible a mayusculas
    
    COMENTARIOS
    - La función transforma automaticamente el numero de ejido a una cadena de 3 digitos completando con ceros.
    - Puede enfocar una circ, radio o manzana si se enlazo correctamente la capa de propietarios. De lo contrario no enfoca nada.

    RETORNO
    Nada
    """
    try:
        dicEjido = BuscarCapasUrbanas(ejido)
        if not dicEjido['ENCARGADO'] or dicEjido['ENCARGADO']=='-':
            print(f'El ejido {ejido} no existe o no esta activo.')
            return
        crs = QgsCoordinateReferenceSystem(dicEjido['EPSG'])
        QgsProject.instance().setCrs(crs)
        #improviso este dicc aca, despues puedo hacerlo mas prolijo importando un csv. O no, qsy
        nombres = {
            'PROPIETARIOS': 'Propietarios-PHs',
            'POSEEDORES': 'Poseedores',
            'EXPEDIENTES': 'Expedientes',
            'MANZANAS': 'Manzanas',
            'RADIOS': 'ORIGEN_RADIOS',
            'CIRCUNSCRIPCIONES': 'ORIGEN_CIRCS',
            'CALLES': 'ORIGEN_CALLES',
            'MEDIDAS-REG': 'ORIGEN_MEDIDAS_REGISTRADOS',
            'MEDIDAS-TITULOS': 'ORIGEN_MEDIDAS_TITULOS',
            'REGISTRADOS': 'Registrados',
        }
        for nombre, valor in nombres.items():
            CANVAS_RepathLayer(valor, dicEjido[nombre], forceCRS=crs)
        
        #a partir de aca empieza la parte de enfocar la seleccion
        capa = CANVAS_CheckForLayer('Propietarios-PHs')
        if not capa:
            return
        capa.selectAll()
        CANVAS_ZoomToSelectedFeatures(capa)

        if circ or radio or cc or mzna:
            capa = CANVAS_CheckForLayer('Propietarios-PHs')
            filtros = {}
            if circ:
                filtros['CIRC'] = circ
            if radio:
                filtros['RADIO'] = radio.upper()
            if cc:
                filtros['CC'] = cc
            if mzna:
                filtros['MZNA'] = str(mzna).upper()
            expresion = ' AND '.join([f"{f}={filters[f]}" if isinstance(filters[f], (int, float)) else f"{f}='{filters[f]}'" for f in filters])
            capa.selectByExpression(expresion)
            CANVAS_ZoomToSelectedFeatures(capa)

    except Exception as e:
        print(f'Ocurrio un error al cambiar al ejido {ejido}. ErrorMSG: {e}')
cambiarejido = CambiarEjido
CAMBIAREJIDO = CambiarEjido

def GenerarBackupCompleto():
    """
    Realiza una copia de seguridad completa de los archivos en las carpetas POLIGONOS, PLANO PUEBLO y EXPEDIENTES de cada ejido.

    PARAMETROS
    Ninguno

    COMENTARIOS
    - La función lee el contenido de las carpetas directamente desde el disco L; guarda todo lo que encuentre.
    - Crea un archivo zip en el directorio de documentos del usuario (Documentos/BACKUPS/), que contiene los archivos.
    - El archivo de salida es alrededor del doble de pesado que usando BackupLigero
    - No genera backup de parcelas rurales.

    RETORNO
    Nada
    """
    directory  = r'L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    if not os.path.exists(directory):
        directory  = r'C:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS'
    files = []
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)) and folder[:3].isdigit() and folder[3] == '-':
            townFolder = os.path.join(directory, folder)
            for subfolder in os.listdir(townFolder):
                if os.path.isdir(os.path.join(townFolder, subfolder)) and (
                     'POLIGONO' in subfolder.upper() or 
                     'PUEBLO' in subfolder.upper() or 
                     'EXPEDIENTE' in subfolder.upper()):
                    files += [os.path.join(townFolder, subfolder, x) for x in os.listdir(os.path.join(townFolder, subfolder))]
    backup_dir = os.path.join(Path.home(), 'Documents', 'BACKUPS')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    zipFile = os.path.join(backup_dir, 'BACKUP GEODESIA ' + STR_GetTimestamp() + '.zip')
    with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in files:
            package.write(file, file) 
Backup = GenerarBackupCompleto
backup = GenerarBackupCompleto
BACKUP = GenerarBackupCompleto

def GenerarBackupLigero():
    """
    Realiza una copia de seguridad de los shapefiles leidos por DicEjidos, de cada ejido.

    PARAMETROS
    Ninguno

    COMENTARIOS
    - La función lee los shapefiles contenidos en la global Dic Ejidos. Deja fuera versiones duplicadas y archivos no necesarios en las caprpetas. Para corroborar, consultar CompletarDicEjidos en DGCFunctions.
    - Crea un archivo zip en el directorio de documentos del usuario, que contiene los archivos encontrados en las carpetas que cumplen con el criterio especificado.
    - No genera backup de parcelas rurales.

    RETORNO
    Nada
    """
    global DicEjidos
    files = []
    for _, val in DicEjidos.items():
        files += val['PROPIETARIOS']
        files += val['POSEEDORES']
        files += val['EXPEDIENTES']
        files += val['MANZANAS']
        files += val['RADIOS']
        files += val['CIRCUNSCRIPCIONES']
        files += val['CALLES']
        files += val['MEDIDAS-REG']
        files += val['MEDIDAS-TITULOS']
        files += val['REGISTRADOS']
    backup_dir = os.path.join(Path.home(), 'Documents', 'BACKUPS')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    zipFile = os.path.join(backup_dir, 'BACKUP GEODESIA ' + STR_GetTimestamp() + '.zip')
    with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in files:
            if file:
                package.write(file, os.path.relpath(file, start=backup_dir)) 
BackupLigero = GenerarBackupLigero
backupligero = GenerarBackupLigero
BACKUPLIGERO = GenerarBackupLigero

def GenerarShapeManzanas(ejido, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
   Genera un shape de Manzanas del ejido indicado. Usa como base el shape de parcelas del ejido.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        Representa el numero del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.
    distanciaBuffer: numero 
        La distancia que debe expanderse y contraerse la capa para eliminar cuñas.
    agregarAlLienzo: booleano
        Si se deja en Verdadero, carga la capa al lienzo de QGis.

    COMENTARIOS
    - Se hacen algunos calculos de antes de disolver; unifica los CC de PH con los de parcelas normales, por ejemplo.
    - Luego de disolver, se intenta eliminar anillos y cuñas medainte buffers

    RETORNOS
    - QgsVectorLayer conteniendo la capa si la funcion tuvo exito
    - Falso si ocurrio un error
    """
    try:
        capa = BuscarCapasUrbanas(ejido)['PROPIETARIOS']
        capa = processing.run('native:fixgeometries', {'INPUT': capa, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'INPUT': capa, 'FIELD_LENGTH' : 0, 'FIELD_NAME' : 'CC', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'IF(cc=4,3,if(cc=5,2,cc))', 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
        # Aun no tengo las expresiones cargadas en el mapa
        # capa = processing.run('native:fieldcalculator', { 'FIELD_LENGTH' : 4, 'FIELD_NAME' : 'MZNA', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 2, 'FORMULA' : 'Quitar0(MZNA)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:dissolve', {'INPUT': capa, 'FIELD' : ['EJIDO','CIRC','RADIO','MZNA','CC'], 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer*-1, 'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa.setName(f'{STR_FillWithChars(ejido,3)}-MANZANAS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar las manzanas del ejido {ejido}. ErrorMSG: {e}')
        return False
RehacerMzs = GenerarShapeManzanas
rehacermzs = GenerarShapeManzanas
REHACERMZS = GenerarShapeManzanas

def GenerarShapeRegistrados(ejido, distanciaBuffer=0.05, agregarAlLienzo=True):
    """
    Genera un shape de Registrados del ejido indicado. Usa como base el shape de parcelas del ejido.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        Representa el numero del ejido. Se rellenará con ceros a la izquierda hasta tener 3 caracteres.
    distanciaBuffer: numero 
        La distancia que debe expanderse y contraerse la capa para eliminar cuñas.
    agregarAlLienzo: booleano
        Si se deja en Verdadero, carga la capa al lienzo de QGis.

    COMENTARIOS
    - Se hacen algunos calculos de antes de disolver; unifica los CC de PH con los de parcelas normales, por ejemplo.
    - Luego de disolver, se intenta eliminar anillos y cuñas medainte buffers

    RETORNOS
    - QgsVectorLayer conteniendo la capa si la funcion tuvo exito
    - Falso si ocurrio un error
    """
    try:
        capas = BuscarCapasUrbanas(ejido)
        capaPropietarios = capas['PROPIETARIOS']
        capaPoseedores = capas['POSEEDORES']
        capa = processing.run('native:mergevectorlayers', { 'CRS' : QgsCoordinateReferenceSystem(''), 'LAYERS' : [capaPropietarios,capaPoseedores], 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fixgeometries', {'INPUT': capa, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        # Aun no tengo las expresiones cargadas en el mapa
        # layer = processing.run('native:fieldcalculator', { 'FIELD_LENGTH' : 4, 'FIELD_NAME' : 'MZNA', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 2, 'FORMULA' : 'Quitar0(MZNA)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'INPUT': capa, 'FIELD_LENGTH' : 0, 'FIELD_NAME' : 'CC', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'IF(cc=4,3,if(cc=5,2,cc))', 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
        capa.setSubsetString('REGISTRADO is not null')
        capa = processing.run('native:dissolve', {'INPUT': capa, 'FIELD' : ['EJIDO','CIRC','RADIO','MZNA','CC','REGISTRADO'], 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer,'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:buffer', {'INPUT': capa, 'DISSOLVE': False, 'DISTANCE': distanciaBuffer*-1,'END_CAP_STYLE': 1, 'JOIN_STYLE': 1, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS' : 1 })['OUTPUT']
        capa = processing.run('native:addfieldtoattributestable', { 'FIELD_LENGTH' : 2, 'FIELD_NAME' : 'COLOR', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 0, 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa = processing.run('native:fieldcalculator', {'FIELD_LENGTH' : 2, 'FIELD_NAME' : 'COLOR', 'FIELD_PRECISION' : 0, 'FIELD_TYPE' : 1, 'FORMULA' : 'rand(1,25)', 'INPUT' : capa, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        capa.setName(f'{STR_FillWithChars(ejido,3)}-REGISTRADOS-{STR_GetTimestamp()}')
        if agregarAlLienzo:
            CANVAS_AddLayer(capa)
        return capa
    except Exception as e:
        print(f'Error al generar los registrados del ejido {ejido}. ErrorMSG: {e}')
        return FalsE
RehacerRegs = GenerarShapeRegistrados
rehacerregs = GenerarShapeRegistrados
REHACERREGS = GenerarShapeRegistrados

def InfoEjido(ejido):
    """
    Imprime en consola la informacion existente sobre el ejido.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        El numero del ejido a mostrar
    """
    dicEjido = BuscarCapasUrbanas(ejido)
    for key, value in dicEjido.items():
        if not value:
            print(f' > {key}: -')
        elif type(value) is str and 'CAD-GIS' in value:
            print(f' > {key}: ..\\{value.split('\\')[-2]}\{value.split('\\')[-1]}')
        else:
            print(f' > {key}: {value}')
info = InfoEjido
Info = InfoEjido
INFO = InfoEjido
infoejido = InfoEjido
INFOEJIDO = InfoEjido

def RecargarInfoEjidos():
    """
    Llena el diccionario con las capas de todos los ejidos.
    """
    CompletarDicEjidos(True)

recargarinfoejidos = RecargarInfoEjidos