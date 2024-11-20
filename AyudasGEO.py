"""
Modulo: AyudasGEO (23 Oct 2024)
Funciones varias para agilizar o automatizar el trabajo diario en Geodesia. Todas las funciones que uso casi a diario, que no supe como encapsular en un modulo con bonito nombre, fueron a parar aca. Cualquier cosa preguntame.
Funciones: 
 > Abrir(registrado) / abrir(12345) / abrir('1234 25222 50789')
- Abre los registrados solicitados.
- Permite abrir un solo registrado o varios en una misma operacion

 > ActualizarShapesPueblo(ejido) / rehacermzsyregs(ejido, 0.05, True, False)
- Genera los shapes de Manzanas y Registrados de un ejido a partir de sus parcelas.
- Por defecto elimina cuñas y anillos mediante buffers a 0.05 unidades (metros), pero se puede cambiar en el primer parametro.
- Por defecto agrega las capas generadas al lienzo, pero puede indicarsele lo contrario asignando False al segundo parametro.
- Por defecto reemplaza las capas de PUEBLOS CAD-GIS con las nuevas, pero puede indicarsele lo contrario asignando False al tercer parametro.

 > CambiarEjido(ejido) / cambiarejido(47, 1, 'q', 3, 51) / 
- Cambia las capas del mapa de trabajo predeterminado al pueblo indicado y lo enfoca.
- Requiere que las capas esten nombradas de la misma forma que la plantilla.
- Los parametros siguientes al ejido son opcionales, permiten construir la nomenclatura de una manzana. El script enfoca al pueblo, luego intenta enfocar a la nomenclatura indicada; puede ser una manzana, radio, etc.
- Por ejemplo, usar cambiarejido(47, 3, 'a') enfocaria al radio A de la circunscripcion III de Santa Rosa.

 > GenerarBackupUrbanoCompleto() / backup()
- Realiza una copia de seguridad completa de los archivos en las carpetas POLIGONOS, PLANO PUEBLO y EXPEDIENTES de cada ejido.
- El archivo .rar generado queda guardado en la carpeta ../Mis Documentos/BACKUPS del usuario actual.

 > GenerarKMZDesdeSeleccion() / kmzdesdesel()
- Genera un archivo KMZ a partir de las parcelas seleccionadas en la capa activa de QGIS.
- El estilo utilizado es el normal de Catastro, es decir, colores segun CC (amarillo, celeste, rojo, verde), sin rellenos, tabla de atributos basicos para el sector Economico.
- El archivo .rar generado queda guardado en la carpeta ../Mis Documentos/BORRAR del usuario actual.

 > GenerarManzanasDesdeSeleccion() / regsdesdesel()
- Genera un shapefile de manzanas parcial como archivo temporal a partir de las parcelas seleccionadas en la capa activa, y lo carga al lienzo.

 > GenerarRegistradosDesdeSeleccion() / mzsdesdesel()
- Genera un shapefile de registrados parcial como archivo temporal a partir de las parcelas seleccionadas en la capa activa, y lo carga al lienzo.

 > InfoEjido(ejido) / info(47)
- Imprime en consola la informacion existente sobre el ejido.

Tipee help(funcion) en la consola para mas informacion.
#################BARRA SEPARADORA DE BAJO PRESUPUESTO#################
"""
import os
import zipfile
import re
import processing
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
    if not capas['PROPIETARIOS']:
        print(f'No encontre los propietarios del ejido {ejido}')
        return
    manzanas = GenerarShapeManzanas(PathToLayer(capas['PROPIETARIOS']), 
                                    STR_FillWithChars(ejido, 3),
                                    distanciaBuffer, 
                                    agregarAlLienzo)
    registrados = GenerarShapeRegistrados([PathToLayer(capas['PROPIETARIOS']), 
                                           PathToLayer(capas['POSEEDORES'])
                                           ], 
                                          STR_FillWithChars(ejido, 3), 
                                          distanciaBuffer, 
                                          agregarAlLienzo)
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
        archivoManzanas = os.path.join(carpeta, f'{manzanas.name()}.shp')
        archivoRegistrados = os.path.join(carpeta, f'{registrados.name()}.shp')
        QgsVectorFileWriter.writeAsVectorFormat(manzanas, archivoManzanas, 'utf-8', driverName='ESRI Shapefile')
        QgsVectorFileWriter.writeAsVectorFormat(registrados, archivoRegistrados, 'utf-8', driverName='ESRI Shapefile')
        DicEjidos[int(ejido)]['MANZANAS'] = archivoManzanas
        DicEjidos[int(ejido)]['REGISTRADOS'] = archivoRegistrados
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
        else:
            iface.setActiveLayer(capa)
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

def GenerarKMZDesdeSeleccion(rutaKml=False):
    """
    Genera un archivo KMZ a partir de las características seleccionadas en la capa activa de QGIS.

    Esta función crea un archivo KMZ que contiene datos KML derivados de las características seleccionadas en la capa activa de QGIS. Utiliza un archivo KML de plantilla, reemplaza un marcador de posición con el contenido KML real y guarda el archivo KML modificado en una ubicación especificada antes de comprimirlo en un archivo KMZ.

    PARAMETROS
    ubicacion: str, opcional
        La ruta donde se guardará el archivo KMZ. Si no se proporciona, se establece de forma predeterminada en la carpeta Documentos/Borrar del usuario, con un timestamp añadido al nombre de la plantilla.

    Devuelve:
        str: La ruta al archivo KMZ generado.
    """
    nombrePlantilla = 'res/Geodesia/KMLBaseDGC'
    archivoPlantilla = PATH_GetFileFromWeb(os.path.join('res','Geodesia',f'{nombrePlantilla}.kml'))
    capa = iface.activeLayer()
    campos = [f.name() for f in capa.fields()]
    if rutaKml:
        pass
    else:
        nombre = re.search(r'\d{3}', capa.source())
        if nombre:
            nombre = f'{nombre.group()}-{capa.name()}-Subset-{STR_GetTimestamp()}.kml'
        else:
            nombre = f'{capa.name()}-Subset-{STR_GetTimestamp()}.kml'
        rutaKml = os.path.join(PATH_GetDefaultSaveFolder(), nombre)
    if 'SECCION' in campos:
        carpetas = KML_ContentBuilder({'NAME':f'{nombre}-Subset' ,'CONTENT':capa}, CalcularNomenclatura, styleBy='StyleCC0', tabs=2, showInTable=['NOMENCLA','PARTIDA','REGISTRADO','APELLIDO','TEN','HECTA','AS','CS'])
    elif 'EJIDO' in campos:
        carpetas = KML_ContentBuilder({'NAME':f'{nombre}-Subset' ,'CONTENT':capa}, CalcularNomenclatura, styleBy='CC', tabs=2, showInTable=['NOMENCLA','PARTIDA','REGISTRADO','CC','APELLIDO','TEN','HECTA','AS','CS'])
    else:
        print('Flaco que mierda me pasaste?')
        return
    with open(archivoPlantilla, 'r+', encoding='utf-8') as plantilla:
        contenido = plantilla.read()
        contenido = contenido.replace('<ContentPlaceholder>', carpetas)
        plantilla.seek(0)
        plantilla.write(contenido)
        plantilla.truncate()
    with open(rutaKml, 'w', encoding='utf-8') as kmz:
        kmz.write(contenido)
    rutaKmz = KML_ToKMZ(rutaKml)
    return rutaKmz
kmzdesdesel = GenerarKMZDesdeSeleccion
KMZDESDESEL = GenerarKMZDesdeSeleccion

def GenerarKMZs(guardarEnL = False):
    """
    Genera los archivos KMZ de todos los pueblos. Los guarda en la carpeta ../Mis Documentos/Borrar del usuario actual

    PARAMETROS

    RETORNO
    """
    fechaYHora = STR_GetTimestamp()
    if guardarEnL:
        carpeta = r'L:/Geodesia/Privado/Sig/PUEBLOS CAD-GIS/KMZs Localidades'
    else:
        carpeta = PATH_GetDefaultSaveFolder()
    carpeta = os.path.join(carpeta, f"KMZs al dia {fechaYHora}")
    nombrePlantilla = 'KMLBaseDGC'
    archivoPlantilla = PATH_GetFileFromWeb(os.path.join('res','Geodesia',f'{nombrePlantilla}.kml'))
    with open(archivoPlantilla, 'r', encoding='utf-8') as archivo:
        plantilla = archivo.read()
    CompletarDicEjidos()
    dicEjidos = LeerDicEjidos()
    kmzs = []
    for _, ejido in dicEjidos.items():
        if ejido['RESPONSABLE']:
            numeroEjido = STR_FillWithChars(ejido['EJIDO'],3)
            nombreEjido = ejido['NOMBRE']
            tipos = ['PROPIETARIOS','POSEEDORES']
            for tipoTen in tipos:
                capa = PathToLayer(ejido[tipoTen])
                if not capa:
                    print(f"No encontre la capa de {tipoTen} en {numeroEjido}")
                    continue
                CANVAS_AddLayer(capa, capa.name())
                nombreKml = f"{numeroEjido}-{nombreEjido}-{tipoTen}.kml"
                carpetaKml = os.path.join(carpeta , f"{numeroEjido}-{nombreEjido}")
                os.makedirs(carpetaKml, exist_ok=True)
                rutaKml = os.path.join(carpetaKml, nombreKml)
                carpetas = KML_ContentBuilder(capa, 
                        CalcularNomenclatura, 
                        styleBy='CC', 
                        tabs=2, 
                        showInTable=['NOMENCLA','PARTIDA','REGISTRADO','CC','APELLIDO','TEN','HECTA','AS','CS'])
                with open(rutaKml, 'w', encoding='utf-8') as kml:
                    contenidoKml = plantilla
                    contenidoKml = contenidoKml.replace('<ContentPlaceholder>', carpetas)
                    kml.write(contenidoKml)
                rutaKmz = KML_ToKMZ(rutaKml)
                CANVAS_RemoveLayerByName(capa.name())
                kmzs.append(rutaKmz)
    return kmzs
kmzs = GenerarKMZs
KMZS = GenerarKMZs

def GenerarManzanero(ejido, circ, radio, cc, mzna, plantilla='Manzanero A4'):
    """
    Genera un manzanero en la nomenclatura especificada, si existe.

    PARAMETROS
    ejido: str
        El nombre del ejido.
    circ: int
        Representa el número de la circunscripción.
    radio: str
        Representa la letra del radio.
    cc: int
        Representa el código catastral.
    mzna: int | str
        Representa la manzana.
    plantilla: str | opcional
        El nombre de la composición (por defecto es 'Manzanero A4').

    COMENTARIOS
    - Esto funciona sobre la plantilla de DGC solamente.
        
    RETORNOS
    None
        La función no devuelve ningún valor. En su lugar, genera una composición en QGIS
        y ajusta el mapa según los parámetros proporcionados.
    """
    if not FiltrarParcelas(circ, radio, cc, mzna):
        return
    capa = QgsProject.instance().mapLayersByName('Propietarios-PHs')[0]
    extension = capa.extent()
    CANVAS_ZoomToLayer(capa)

    manager = QgsProject.instance().layoutManager()
    composicion = manager.layoutByName(plantilla)
    if composicion is not None:
        iface.openLayoutDesigner(composicion)
    else:
        print(f"No se encontró una composición con el nombre {plantilla}")

    mapa = composicion.itemById('ventanaGrafica')
    mapa.zoomToExtent(extension)
    mapa.setScale(NUM_GetNextScale(mapa.scale(), 1.15))

    if cc == 1:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-Ch.{str(mzna)}"
    elif cc == 2 or cc == 5:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-{radio.lower()}-Qt.{str(mzna)}"
    else:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-{radio.lower()}-Mz.{str(mzna)}"
    texto = composicion.itemById('Nombre')
    texto.setText(nomencla)
    texto.refresh()
    
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
                print(f" > {key}: .." + "\\" + value.split('\\')[-2] + "\\" + value.split('\\')[-1])
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