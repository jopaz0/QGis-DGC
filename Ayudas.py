"""
Modulo: Ayudas (23 Oct 2024)
Funciones varias para agilizar o automatizar el trabajo diario en DGC.
Funciones: 
 > Backup
Tipee help(funcion) en la consola para mas informacion.
"""
import os, zipfile
from pathlib import Path
from CommonFunctions import * # STR_GetTimestamp

def Backup():
    """
    Realiza una copia de seguridad de los archivos en las carpetas POLIGONOS Y PLANO PUEBLO de cada ejido.

    PARAMETROS
    Ninguno

    COMENTARIOS
    - La función busca en el directorio L:\Geodesia\Privado\Sig\PUEBLOS CAD-GIS aquellos que comienzan con tres números seguidos de un guion. 
    - Crea un archivo zip en el directorio de documentos del usuario, que contiene los archivos encontrados en las carpetas que cumplen con el criterio especificado.

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
                if os.path.isdir(os.path.join(townFolder, subfolder)) and 'POLIGONOS' in subfolder.upper() or 'PUEBLO' in subfolder.upper():
                    files += [os.path.join(townFolder, subfolder, x) for x in os.listdir(os.path.join(townFolder, subfolder))]
    backup_dir = os.path.join(Path.home(), 'Documents', 'BACKUPS')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    zipFile = os.path.join(backup_dir, 'BACKUP GEODESIA ' + STR_GetTimestamp() + '.zip')
    with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED) as package:
        for file in files:
            package.write(file, os.path.relpath(file, start=backup_dir)) 
backup = Backup
BACKUP = Backup