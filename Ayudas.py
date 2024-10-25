"""
Modulo: Ayudas (23 Oct 2024)
Funciones varias para agilizar o automatizar el trabajo diario en DGC.
Funciones: 
 > Abrir
 > ActualizarShapesPueblo / rehacermzsyregs
 > CambiarEjido
 > GenerarBackupUrbanoCompleto / backup
 > GenerarRegistradosDesdeSeleccion / mzsdesdesel
 > GenerarManzanasDesdeSeleccion / regsdesdesel
 > InfoEjido / info
Tipee help(funcion) en la consola para mas informacion.

Fomentando la vagancia responsable desde 2017!
"""
import os, zipfile
from pathlib import Path
from qgis.utils import *
from qgis.gui import *
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
        encontrado = False
        try:
            path = os.path.join(directory, f'{reg[0:2]}.000', f'{reg[0:2]}.{reg[2]}00')
            if os.path.exists(path):
                for file in os.listdir(path):
                    if f'{reg[0:2]}.{reg[2:]}' in file and file.endswith('.pdf'):
                        os.startfile(os.path.join(path, file))
                        encontrado = True
                if not encontrado:
                    print(f'No encontre el registrado {reg[0:2]}.{reg[2:]}.pdf')
                    #iface.messageBar().pushMessage("Advertencia", f'No se encontro El PDF {reg}', level=Qgis.Warning)
            else:
                print(f'No encontre la carpeta {path}.')
                #iface.messageBar().pushMessage("Advertencia", f'No se encontro la carpeta {path}', level=Qgis.Warning)
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
    global DicEjidos
    ejido = int(ejido)
    capas = BuscarCapasUrbanas(ejido)
    manzanas = GenerarShapeManzanas(capas['PROPIETARIOS'], STR_FillWithChars(ejido, 3),distanciaBuffer, agregarAlLienzo)
    registrados = GenerarShapeRegistrados([capas['PROPIETARIOS'], capas['POSEEDORES']], STR_FillWithChars(ejido, 3), distanciaBuffer, agregarAlLienzo)
    if not sustituirCapas:
        return
    carpeta = os.path.dirname(capas['MANZANAS'])
    capasViejas = [os.path.join(carpeta, archivo) for archivo in os.listdir(carpeta) if 'MANZANA' in archivo.upper() or 'REGISTRADO' in archivo.upper()]
    for capa in capasViejas:
        try:
            os.remove(capa)
        except Exception as e:
            print(f'No pude eliminar {capa}. ErrorMSG: {e}')
    try:
        QgsVectorFileWriter.writeAsVectorFormat(manzanas, os.path.join(carpeta, f'{manzanas.name()}.shp'), 'utf-8', driverName='ESRI Shapefile')
        QgsVectorFileWriter.writeAsVectorFormat(registrados, os.path.join(carpeta, f'{registrados.name()}.shp'), 'utf-8', driverName='ESRI Shapefile')
        DicEjidos[int(ejido)]['MANZANAS'] = manzanas.source()
        DicEjidos[int(ejido)]['REGISTRADOS'] = registrados.source()
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
        if not dicEjido['RESPONSABLE'] or dicEjido['RESPONSABLE']=='-':
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
            expresion = ' AND '.join([f"{f}={filtros[f]}" if isinstance(filtros[f], (int, float)) else f"{f}='{filtros[f]}'" for f in filtros])
            capa.selectByExpression(expresion)
            CANVAS_ZoomToSelectedFeatures(capa)

    except Exception as e:
        print(f'Ocurrio un error al cambiar al ejido {ejido}. ErrorMSG: {e}')
cambiarejido = CambiarEjido
CAMBIAREJIDO = CambiarEjido

def GenerarBackupUrbanoCompleto():
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
    zipFile = os.path.join(backup_dir, 'BACKUP PUEBLOS COMPLETO ' + STR_GetTimestamp() + '.zip')
    with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in files:
            package.write(file, file) 
Backup = GenerarBackupUrbanoCompleto
backup = GenerarBackupUrbanoCompleto
BACKUP = GenerarBackupUrbanoCompleto

def GenerarBackupUrbanoLigero():
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
    zipFile = os.path.join(backup_dir, 'BACKUP PUEBLOS LIGERO ' + STR_GetTimestamp() + '.zip')
    with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in files:
            if file:
                package.write(file, os.path.relpath(file, start=backup_dir)) 
BackupLigero = GenerarBackupUrbanoLigero
backupligero = GenerarBackupUrbanoLigero
BACKUPLIGERO = GenerarBackupUrbanoLigero

def GenerarManzanasDesdeSeleccion():
    """
    Genera un shapefile de manzanas parcial como archivo temporal, a partir de las parcelas seleccionadas en la capa activa.

    PARAMETROS

    COMENTARIOS

    RETORNO
    """
    capa = iface.activeLayer()
    if not capa.selectedFeatures():
        print(f'No habia parcelas seleccionadas en {capa.name()}')
        return
    capa = processing.run('native:fixgeometries', {'INPUT': QgsProcessingFeatureSourceDefinition(capa.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid), 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
    GenerarShapeManzanas(capa, 'temp')
mzsdesdesel = GenerarManzanasDesdeSeleccion
MZSDESDESEL = GenerarManzanasDesdeSeleccion

def GenerarRegistradosDesdeSeleccion():
    """
    Genera un shapefile de registrados parcial como archivo temporal, a partir de las parcelas seleccionadas en la capa activa.

    PARAMETROS

    COMENTARIOS

    RETORNO
    """
    capa = iface.activeLayer()
    if not capa.selectedFeatures():
        print(f'No habia parcelas seleccionadas en {capa.name()}')
        return
    capa = processing.run('native:fixgeometries', {'INPUT': QgsProcessingFeatureSourceDefinition(capa.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid), 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
    GenerarShapeRegistrados([capa], 'temp')
regsdesdesel = GenerarRegistradosDesdeSeleccion
REGSDESDESEL = GenerarRegistradosDesdeSeleccion

def InfoEjido(ejido=False):
    """
    Imprime en consola la informacion existente sobre el ejido o los modulos.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        El numero del ejido a mostrar
    """
    if not ejido:
        import Digitalizacion
        import Sincronizacion
        import Ayudas
        help(Digitalizacion)
        help(Sincronizacion)
        help(Ayudas)
    else:
        dicEjido = BuscarCapasUrbanas(ejido)
        for key, value in dicEjido.items():
            if key == 'NUMERO':
                print(f' > {key}: {STR_FillWithChars(value, 3)}')
            elif not value:
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