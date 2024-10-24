"""
Modulo: Ayudas (23 Oct 2024)
Funciones varias para agilizar o automatizar el trabajo diario en DGC.
Funciones: 
 > Abrir
 > Backup
 > CambiarEjido
 > ActualizarShapesPueblo / rehacermzsyregs
Tipee help(funcion) en la consola para mas informacion.
"""
import os, zipfile
from pathlib import Path
from CommonFunctions import * # STR_GetTimestamp
from DGCFunctions import * # BuscarCapasUrbanas

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

def Backup():
    """
    Realiza una copia de seguridad de los shapefiles de cada ejido.

    PARAMETROS
    Ninguno

    COMENTARIOS
    - La función busca en el directorio L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS aquellos que comienzan con tres números seguidos de un guion, es decir las carpetas de los pueblos. 
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
backup = Backup
BACKUP = Backup

def CambiarEjido (ejido, circ = False, radio = False):
    """
    Cambia las capas del mapa de trabajo predeterminado al pueblo indicado y lo enfoca. Puede filtrar las parcelas por CIRC y RADIO.

    PARAMETROS
    ejido: numero entero o cadena de caracteres
        El numero del ejido a mostrar
    circ: numero entero
        Opcional, la circunscripcion a filtrar
    radio: caracter
        Opcional, el radio a filtrar 
    
    COMENTARIOS
    - La función transforma automaticamente el numero de ejido a una cadena de 3 digitos completando con ceros.

    RETORNO
    Nada
    """
    try:
        dicEjido = BuscarCapasUrbanas(ejido)
        if not dicEjido['NOMBRE'] or dicEjido['NOMBRE']=='-':
            print(f'El ejido {ejido} no existe?')
            return
        filtros = {}
        if circ:
            filtros['CIRC'] = circ
        if radio:
            filtros['RADIO'] = radio
        #improviso esto aca, despues puedo hacerlo mas prolijo. O no, qsy
        nombres = {
            'PROPIETARIOS': ['Propietarios-PHs', filtros],
            'POSEEDORES': ['Poseedores', filtros],
            'EXPEDIENTES': ['Expedientes', {}],
            'MANZANAS': ['Manzanas', filtros],
            'RADIOS': ['ORIGEN_RADIOS', {}],
            'CIRCUNSCRIPCIONES': ['ORIGEN_CIRCS', {}],
            'CALLES': ['ORIGEN_CALLES', {}],
            'MEDIDAS-REG': ['ORIGEN_MEDIDAS_REGISTRADOS', filtros],
            'MEDIDAS-TITULOS': ['ORIGEN_MEDIDAS_TITULOS', filtros],
            'REGISTRADOS': ['Registrados', filtros],
        }
        for nombre, valor in nombres.items():
            CANVAS_RepathLayer(valor[0], dicEjido[nombre], valor[1])
        
        capa = CANVAS_CheckForLayer('Propietarios-PHs')
        capa.selectAll()
        extent = capa.boundingBoxOfSelected()
        if not extent.isEmpty():
            iface.mapCanvas().setExtent(extent)
            iface.mapCanvas().refresh()
        capa.removeSelection()
    except Exception as e:
        print(f'Ocurrio un error al cambiar al ejido {ejido}. ErrorMSG: {e}')
cambiarejido = CambiarEjido
CAMBIAREJIDO = CambiarEjido

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
