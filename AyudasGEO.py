"""
Modulo: AyudasGEO
Funciones varias para agilizar o automatizar el trabajo diario en Geodesia.
"""
import os
import zipfile
import re
import processing
import time
from uuid import uuid4
from pathlib import Path
from qgis.utils import *
from qgis.gui import *
from qgis.core import *
from qgis.PyQt.QtCore import QTimer
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
    
@RegisterFunction("abrir", "ABRIR", "ab", "AB")
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

@RegisterFunction("abrirs", "ABRIRS", "abrs", "ABRS")
def AbrirDesdeSeleccion(campo="REGISTRADO", capa=None):
    """
    Abre los registrados de las parcelas (?) seleccionadas en la capa actual.

    PARAMETROS
    campo: nombre del campo donde estan almacenados los registrados, pasado como cadena. Por defecto, usa 'REGISTRADO'.
    capa: la capa desde la cual leer los registrados, pasada como QgsVectorLayer. Por defecto, usa la actual.
    
    COMENTARIOS
    - La función invoca a Abrir() con la lista de registrados como parametro.

    RETORNO
    Nada
    """
    if capa is None:
        capa = iface.activeLayer()
    if not capa:
        raise Exception("No hay capa activa")
    if capa.selectedFeatureCount() == 0:
        raise Exception("No hay objetos seleccionados")
    valores = []
    for f in capa.selectedFeatures():
        valor = f[campo]
        if valor:
            partes = [int(x) for x in str(valor).split("-") if x.strip().isdigit()]
            valores.extend(partes)
    valores = sorted(set(valores))
    abrir("-".join(str(v) for v in valores))

@RegisterFunction("RehacerMzsYRegs", "rehacermzsyregs", "REHACERMZSYREGS")
def ActualizarShapesPueblo(ejido, distanciaBuffer=0.05, agregarAlLienzo=True, sustituirCapas=False):
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

@RegisterFunction("cambiarejido", "CAMBIAREJIDO", "ce", "CE")
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
            #'PROPIETARIOS': 'PARCELAS',
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

@RegisterFunction("completarcampomedidas", "COMPLETARCAMPOMEDIDAS", "ccm", "CCM")
def CompletarCampoMedidas(sobreescribir=False, textoAdvertencia=False, campoMedidas='MEDIDAS', campoId='NOMENCLA'):
    """
    Completa el campo de medidas en los objetos seleccionados de la capa activa.

    PARAMETROS
    sobreescribir: bool
        Opcional, determina si sobreescribir las medidas existentes o ignorar esos poligonos. Por defecto los ignora.
    textoAdvertencia: cadena de caracteres
        Opcional, inserta ese texto al inicio de la primer medida, como recordatorio que las medidas estan sin corroborar con el plano. 
        Por defecto no inserta nada.
    campoMedidas: cadena de caracteres
        Opcional, el nombre del campo donde guardar las medidas. Por defecto guarda en MEDIDAS
    campoId: cadena de caracteres
        Opcional, el nombre del campo que identifica a cada objeto. Por defecto usa NOMENCLA

    COMENTARIOS

    RETORNO
    Nada
    """

    #compruebo el input, por las dudas
    capa = iface.activeLayer()
    if not capa:
        print('No se selecciono una capa.')
        print('Seleccione una capa en el arbol de capas, y reintente.')
        return
    if capa.isEditable():    
        print('La capa seleccionada estaba en edicion.')
        print('Guarde/cancele los cambios, conmute la edicion, y reintente.')
        return
    if not capa.selectedFeatures():
        print(f'No habia objetos seleccionados en {capa.name()}.')
        return
    camposCapa = [f.name() for f in capa.fields()]
    if not campoMedidas in camposCapa:
        print(f'El campo {campoMedidas} no existe en {capa.name()}.')
        return
    if not campoId in camposCapa:
        print(f'El campo {campoId} no existe en {capa.name()}.')
        return
        
    #me hago un diccionario con los objetos seleccionados
    objetos = {}
    for objeto in capa.selectedFeatures():
        objetos[objeto[campoId]] = objeto
    if not sobreescribir:
        ignorados = 0
        for key, objeto in objetos.items():
            if str(objeto[campoMedidas])!='NULL' and str(objeto[campoMedidas])!='':
                objetos[key] = False
                ignorados += 1
    
    #separo lo seleccionado en una capa temporal y la uso para calcular las medidas
    params = {  'INPUT': QgsProcessingFeatureSourceDefinition(capa.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid), 
                'OUTPUT':'TEMPORARY_OUTPUT'}
    capaClonada = processing.run('native:fixgeometries', params)['OUTPUT']
    capaClonada = LAY_Simplify(LAY_ForceRHR(capaClonada), 0.02)
    for clon in capaClonada.getFeatures():
        geom = GEOM_NormalizeFirstVertex(clon.geometry())
        medidas = GEOM_GetMeasuresString(geom)
        medidas = medidas.replace('.00','')
        if textoAdvertencia:
            medidas = textoAdvertencia + medidas
        with edit(capa):
            if objetos[clon[campoId]]:
                objetos[clon[campoId]][campoMedidas] = medidas
                capa.updateFeature(objetos[clon[campoId]])
    capa.removeSelection()
    if ignorados:
        print(f'Ignorados {ignorados} objetos que ya tenian medidas cargadas.')
    return

@RegisterFunction("fcs", "FCS")
def FiltrarCoordenadasPorSeleccion(layerNames=["Coordenadas de Registrados","Coordenadas agregadas"]):
    layer = iface.activeLayer()
    if not layer:
        raise Exception("No hay capa activa.")
    selected = layer.selectedFeatures()
    if not selected:
        raise Exception("No hay elementos seleccionados en la capa activa.")
    feat = selected[0]
    registrado_val = feat["REGISTRADO"]
    for name  in layerNames:
        coords_layer = QgsProject.instance().mapLayersByName(name)
        if not coords_layer:
            raise Exception("No se encontró la capa '" + name + "'.")
        coords_layer = coords_layer[0]
        if registrado_val is None:
            filtro = '"REGISTRADO" is null'
        else:
            filtro = f'"REGISTRADO" is null OR "REGISTRADO" = {registrado_val}'
        coords_layer.setSubsetString(filtro)
    abrir(registrado_val)
    print(f"Filtro aplicado: {filtro}")

@RegisterFunction("Backup", "backup", "BACKUP")
def Backups(rutaBackup=r'L:\Geodesia\Privado\Opazo\Backups'):
    """
    Realiza una copia de seguridad de las parcelas urbanas  y de las parcelas con medidas o mas de un registrado.
    """
    if not rutaBackup:
        BackupCapasUrbanas()
        BackupMedidasYRegistradosUrbanos()
    else:
        BackupCapasUrbanas(rutaBackup)
        BackupMedidasYRegistradosUrbanos(rutaBackup)
    
@RegisterFunction("mzsdesdesel", "MZSDESDESEL")
def GenerarManzanasDesdeSeleccion(capa=False):
    """
    Genera un shapefile de manzanas parcial como archivo temporal, a partir de las parcelas seleccionadas en la capa activa.

    PARAMETROS

    COMENTARIOS

    RETORNO
    """
    if not capa:
        capa = iface.activeLayer()
    if capa.selectedFeatures():
        capa = processing.run('native:fixgeometries', {'INPUT': QgsProcessingFeatureSourceDefinition(capa.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid), 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
    GenerarShapeManzanas(capa, 'temp')

@RegisterFunction("regsdesdesel", "REGSDESDESEL")
def GenerarRegistradosDesdeSeleccion(capa=False):
    """
    Genera un shapefile de registrados parcial como archivo temporal, a partir de las parcelas seleccionadas en la capa activa.

    PARAMETROS

    COMENTARIOS

    RETORNO
    """
    if not capa:
        capa = iface.activeLayer()
    if capa.selectedFeatures():
        capa = processing.run('native:fixgeometries', {'INPUT': QgsProcessingFeatureSourceDefinition(capa.id(), selectedFeaturesOnly=True, featureLimit=-1, geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid), 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
    GenerarShapeRegistrados([capa], 'temp')

@RegisterFunction("kmzdesdesel", "KMZDESDESEL")
def GenerarKMZDesdeSeleccion(rutaKml=False, decorarNomencla = False):
    """
    Genera un archivo KMZ a partir de las características seleccionadas en la capa activa de QGIS.

    Esta función crea un archivo KMZ que contiene datos KML derivados de las características seleccionadas en la capa activa de QGIS. Utiliza un archivo KML de plantilla, reemplaza un marcador de posición con el contenido KML real y guarda el archivo KML modificado en una ubicación especificada antes de comprimirlo en un archivo KMZ.

    PARAMETROS
    ubicacion: str, opcional
        La ruta donde se guardará el archivo KMZ. Si no se proporciona, se establece de forma predeterminada en la carpeta Documentos/Borrar del usuario, con un timestamp añadido al nombre de la plantilla.

    Devuelve:
        str: La ruta al archivo KMZ generado.
    """
    generadorNombres = CalcularNomenclatura if decorarNomencla else CalcularNomenclaturaInterna
    nombrePlantilla = 'KMLBaseDGC'
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
        carpetas = KML_ContentBuilder({'NAME':f'{nombre}-Subset' ,'CONTENT':capa}, generadorNombres, styleBy='StyleCC0', tabs=2, showInTable=['NOMENCLA','PARTIDA','REGISTRADO','APELLIDO','TEN','HECTA','AS','CS'])
    elif 'EJIDO' in campos:
        carpetas = KML_ContentBuilder({'NAME':f'{nombre}-Subset' ,'CONTENT':capa}, generadorNombres, styleBy='CC', tabs=2, showInTable=['NOMENCLA','PARTIDA','REGISTRADO','CC','APELLIDO','TEN','HECTA','AS','CS'])
    else:
        print('Flaco que mierda me pasaste?')
        return
    with open(archivoPlantilla, 'r', encoding='utf-8') as plantilla:
        contenido = plantilla.read()
        #contenido = contenido.replace('<ContentPlaceholder>', carpetas)
        #plantilla.seek(0)
        #plantilla.write(contenido)
        #plantilla.truncate()
    with open(rutaKml, 'w', encoding='utf-8') as kmz:
        kmz.seek(0)
        kmz.write(contenido)
        kmz.truncate()
        contenido = contenido.replace('<ContentPlaceholder>', carpetas)
        kmz.write(contenido)
    rutaKmz = KML_ToKMZ(rutaKml)
    return rutaKmz

@RegisterFunction("kmzs", "KMZS", "generarkmzs", "GENERARKMZS")
def GenerarKMZs(guardarEnL = False, decorarNomencla = False):
    """
    Genera los archivos KMZ de todos los pueblos. Los guarda en la carpeta ../Mis Documentos/Borrar del usuario actual

    PARAMETROS

    RETORNO
    """
    generadorNombres = CalcularNomenclatura if decorarNomencla else CalcularNomenclaturaInterna
    fechaYHora = STR_GetTimestamp()
    if guardarEnL:
        carpeta = r'L:/Geodesia/Privado/Sig/PUEBLOS CAD-GIS/KMZs Localidades'
    else:
        carpeta = PATH_GetDefaultSaveFolder()
    carpeta = os.path.join(carpeta, f"KMZs al dia {fechaYHora}")
    nombrePlantilla = 'KMLBaseDGC'
    #archivoPlantilla = PATH_GetFileFromWeb(os.path.join('res','Geodesia',f'{nombrePlantilla}.kml'))
    archivoPlantilla = r'L:/Geodesia/Privado/Opazo/Weas Operativas/Scripts/res/Geodesia/KMLBaseDGC.kml'
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
                        generadorNombres, 
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

@RegisterFunction("generarmanzanero", "GENERARMANZANERO", "gmz", "GMZ")
def GenerarManzanero(ejido, circ, radio, cc, mzna, rotarMapa=False, plantilla='Manzanero A4'):
    """
    Genera un manzanero en la nomenclatura especificada, si existe.

    PARAMETROS
    ejido: str | int
        El numero del ejido.
    circ: int
        Representa el número de la circunscripción.
    radio: str
        Representa la letra del radio.
    cc: int
        Representa el código catastral.
    mzna: int | str
        Representa la manzana.
    rotarMapa: bool | opcional
        Indica si rotar la vista del mapa en la composicion.
        Aun tiene algunos problemas con la visualizacion de las etiquetas.
    plantilla: str | opcional
        El nombre de la composición (por defecto es 'Manzanero A4').

    COMENTARIOS
    - Esto funciona solamente sobre un proyecto vacio.
        
    RETORNOS
    None
        La función no devuelve ningún valor. En su lugar, genera una composición en QGIS
        y ajusta el mapa según los parámetros proporcionados.
    """
    if QgsProject.instance().mapLayers():
        print('Hay capas cargadas en el proyecto!')
        print('Intente de nuevo en un proyecto vacio.')
        return
    
    plantillaComposicion = PATH_GetFileFromWeb(['res', 'Geodesia', plantilla+'.qpt'])
    PROJ_ImportGPL(PATH_GetFileFromWeb(['res', 'Geodesia', 'Colores Qgis.gpl']))
    filtro = f'"CIRC"={circ} AND "RADIO" ILIKE \'{radio}\' AND "CC"={cc} AND "MZNA" ilike \'{str(mzna)}\''
    capas = BuscarCapasUrbanas(ejido)
    
    #Cargo las capas en el orden que las necesito
    macizos = GenerarShapeManzanas(PathToLayer(capas['PROPIETARIOS']), 'temp')
    registrados = GenerarShapeRegistrados([PathToLayer(capas['PROPIETARIOS']),PathToLayer(capas['POSEEDORES'])], 'temp')
    propietarios = CANVAS_AddLayer(capas['PROPIETARIOS'])
    poseedores = CANVAS_AddLayer(capas['POSEEDORES'])
    clonPropietarios = CANVAS_AddLayer(processing.run('native:fixgeometries', {'INPUT' : propietarios, 'METHOD' : 1, 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT'])
    clonPoseedores = CANVAS_AddLayer(processing.run('native:fixgeometries', {'INPUT' : poseedores, 'METHOD' : 1, 'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT'])
    radios = CANVAS_AddLayer(capas['RADIOS'])
    circs = CANVAS_AddLayer(capas['CIRCUNSCRIPCIONES'])
    calles = CANVAS_AddLayer(capas['CALLES'])

    #renombro las capas
    macizos.setName('TEMP Macizos')
    registrados.setName('TEMP Registrados')
    propietarios.setName('ORIGINAL!!! Propietarios')
    clonPropietarios.setName('TEMP Propietarios')
    poseedores.setName('ORIGINAL!!! Poseedores')
    clonPoseedores.setName('TEMP Poseedores')
    radios.setName('ORIGINAL!!! Radios')
    circs.setName('ORIGINAL!!! Circs')
    calles.setName('ORIGINAL!!! Calles')
    
    #Apago las originales de propietarios y poseedores
    arbolCapas = QgsProject.instance().layerTreeRoot()
    arbolCapas.findLayer(propietarios.id()).setItemVisibilityChecked(False)
    arbolCapas.findLayer(poseedores.id()).setItemVisibilityChecked(False)
    
    #Aplico filtros a parcelas y registrados
    propietarios.setSubsetString(filtro)
    poseedores.setSubsetString(filtro)
    clonPropietarios.setSubsetString(filtro)
    clonPoseedores.setSubsetString(filtro)
    registrados.setSubsetString(filtro)
    
    #Aplico estilos predefinidos 
    propietarios.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Propietarios.qml']))
    clonPropietarios.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Propietarios.qml']))
    poseedores.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Poseedores.qml']))
    clonPoseedores.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Poseedores.qml']))
    radios.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Radios.qml']))
    circs.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Circunscripciones.qml']))
    calles.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Calles.qml']))
    macizos.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Macizos.qml']))
    registrados.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Manz-Registrados.qml']))
    
    #pequeña espera a que qgis cargue las capas en lienzo
    QTimer.singleShot(200, lambda: CANVAS_ZoomToLayer(propietarios))
    
    #Atando con alambre para que no se repitan tanto los colores...
    with edit(registrados):
        counter = 1
        for f in registrados.getFeatures():
            f['COLOR'] = counter%25+1
            registrados.updateFeature(f)
            counter += 1
    
    #Roto la visa de mapa...
    if rotarMapa:
        angulo = LAY_GetOMBBAngle(clonPropietarios)
        iface.mapCanvas().setRotation(angulo)
    
    #busco la plantilla de manzanero
    if os.path.exists(plantillaComposicion):
        PROJ_ImportLayout(plantillaComposicion, plantilla)
    else:
        print(f'No se encontro {plantillaComposicion}.')
        return
    
    #configuro la vista del mapa y renombro la nomenclatura
    manager = QgsProject.instance().layoutManager()
    composicion = manager.layoutByName(plantilla)
    iface.openLayoutDesigner(composicion)
    mapa = composicion.itemById('ventanaGrafica')
    mapa.zoomToExtent(propietarios.extent())
    mapa.setScale(NUM_GetNextScale(mapa.scale(), 1.2))
    if rotarMapa:
        mapa.setMapRotation(angulo)
    if cc == 1:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-Ch.{str(mzna)}"
    elif cc == 2 or cc == 5:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-{radio.lower()}-Qt.{str(mzna)}"
    else:
        nomencla = f"{STR_FillWithChars(ejido,3)}-{STR_IntToRoman(circ)}-{radio.lower()}-Mz.{str(mzna)}"
    texto = composicion.itemById('Nombre')
    texto.setText(nomencla)
    texto.refresh()

@RegisterFunction("generarplanopueblo", "GENERARPLANOPUEBLO", "gpp", "GPP")
def GenerarPlanoPueblo(ejido, plantilla='Pueblo A1', ruta=False, hacerMierdaTodo=False):
    """
    Genera un plano de pueblo del ejido provisto.

    PARAMETROS
    ejido: str | int
        El numero del ejido.
    ruta: str
        La ruta donde guardar el PDF.
    plantilla: str | opcional
        El nombre de la composición plantilla (por defecto es 'Manzanero A4').

    COMENTARIOS
    - Esto funciona solamente sobre un proyecto vacio.
        
    RETORNOS
    None
        La función no devuelve ningún valor. En su lugar, genera una composición en QGIS
        y ajusta el mapa según los parámetros proporcionados.
    """
    def aplicarEscalas(myes):#mapas y escalas, [[mapa, escala],[mapa, escala]]
        for mye in myes:
            mye[0].setScale(mye[1])
            mye[0].refresh()
        
    if QgsProject.instance().mapLayers():
        if hacerMierdaTodo:
        #se pudre todo
            CANVAS_RemoveLayersContaining('')
        else:
            print('Hay capas cargadas en el proyecto!')
            print('Intente de nuevo en un proyecto vacio.')
            return
    
    plantillaComposicion = PATH_GetFileFromWeb(['res', 'Geodesia', plantilla+'.qpt'])
    infoEjido = BuscarCapasUrbanas(ejido)
    if not infoEjido['PROPIETARIOS']:
        print('Existe ese ejido?')
        return False
    
    crs = QgsCoordinateReferenceSystem(infoEjido['EPSG'])
    QgsProject.instance().setCrs(crs)
    
    #Cargo las capas en el orden que las necesito
    registrados = CANVAS_AddLayer(GenerarShapeRegistrados([PathToLayer(infoEjido['PROPIETARIOS']),PathToLayer(infoEjido['POSEEDORES'])], 'temp'))
    poseedores = CANVAS_AddLayer(infoEjido['POSEEDORES'])
    propietarios = CANVAS_AddLayer(infoEjido['PROPIETARIOS'])
    radios = CANVAS_AddLayer(infoEjido['RADIOS'])
    circs = CANVAS_AddLayer(infoEjido['CIRCUNSCRIPCIONES'])
    macizos = CANVAS_AddLayer(GenerarShapeManzanas(PathToLayer(infoEjido['PROPIETARIOS']), 'temp'))
    try:
        calles = CANVAS_AddLayer(GenerarShapeCallesSegmentadas(infoEjido['CALLES']))
    except:
        print('No pude generar el shapefile de calles segmentadas. Cambiando al original...')
        calles = CANVAS_AddLayer(infoEjido['CALLES'])
    radiosMini = CANVAS_AddLayer(infoEjido['RADIOS'])
    circsMini = CANVAS_AddLayer(infoEjido['CIRCUNSCRIPCIONES'])
        
    #renombro las capas
    macizos.setName('TEMP Macizos')
    registrados.setName('TEMP Registrados')
    propietarios.setName('ORIGINAL!!! Propietarios')
    poseedores.setName('ORIGINAL!!! Poseedores')
    radios.setName('ORIGINAL!!! Radios')
    circs.setName('ORIGINAL!!! Circs')
    calles.setName('ORIGINAL!!! Calles')
    radiosMini.setName('ORIGINAL!!! Radios Mini')
    circsMini.setName('ORIGINAL!!! Circs Mini')
    
    #Aplico estilos predefinidos 
    propietarios.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Propietarios.qml']))
    poseedores.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Poseedores.qml']))
    radios.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Radios.qml']))
    circs.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Circunscripciones.qml']))
    calles.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Calles.qml']))
    macizos.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Macizos.qml']))
    registrados.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Registrados.qml']))
    radiosMini.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Mini-Radios.qml']))
    circsMini.loadNamedStyle(PATH_GetFileFromWeb(['res', 'Geodesia','Pueb-Mini-Circunscripciones.qml']))
    
    #creo los temas de mapa
    capasPueblo = [propietarios, poseedores, radios, circs, calles, macizos, registrados]
    capasMini = [radiosMini, circsMini]
    for capa in capasMini:
        QgsProject.instance().layerTreeRoot().findLayer(capa.id()).setItemVisibilityChecked(False)
    PROJ_CreateThemeWithCurrentState('PUEBLO') 
    for capa in capasMini:
        QgsProject.instance().layerTreeRoot().findLayer(capa.id()).setItemVisibilityChecked(True)
    for capa in capasPueblo:
        QgsProject.instance().layerTreeRoot().findLayer(capa.id()).setItemVisibilityChecked(False)
    PROJ_CreateThemeWithCurrentState('MINI') 
    
    #pequeña espera a que qgis cargue las capas en lienzo
    QTimer.singleShot(500, lambda: CANVAS_ZoomToLayer(propietarios))
    
    #busco la plantilla de la composicion, la cargo, valido y abro
    if os.path.exists(plantillaComposicion):
        PROJ_ImportLayout(plantillaComposicion, plantilla)
        manager = QgsProject.instance().layoutManager()
        composicion = manager.layoutByName(plantilla)
        for item in composicion.items():
            try:
                if not item.id():
                    nuevoID = f"item_{uuid4().hex}"
                    item.setId(nuevoID)
            except:
                pass
        iface.openLayoutDesigner(composicion)
    else:
        print(f'No se encontro {plantillaComposicion}.')
        return
    
    #Zooms
    mapaPueblo = composicion.itemById('ventanaGrafica')
    mapaMini = composicion.itemById('mini')
    mapaPueblo.zoomToExtent(propietarios.extent())
    mapaMini.zoomToExtent(radiosMini.extent())
    mapaPueblo.refresh()
    mapaMini.refresh()
    escPueblo = infoEjido['ESCPUEBLO']
    escMini = infoEjido['ESCMINI']
    QTimer.singleShot(1500, lambda: aplicarEscalas([[mapaPueblo,escPueblo],[mapaMini,escMini],[mapaPueblo,escPueblo]]))
    
    #nombre
    nombre = STR_FillWithChars(ejido,3) + '\n' + infoEjido['NOMBRE']
    texto = composicion.itemById('nombre')
    texto.setText(nombre)
    texto.refresh()
    
    if ruta:
        ruta = os.path.join(Path.home(),'Documents','BORRAR')
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        nombre = nombre.replace(' ','') + '-' + STR_GetTimestamp() + '.pdf'
        ruta = os.path.join(ruta, nombre)
        exportador = QgsLayoutExporter(composicion)
        exportador.exportToPdf(ruta, QgsLayoutExporter.PdfExportSettings())
        print(f'Plano de pueblo guardado en {ruta}.')
    if infoEjido['OBSERVACIONES']:
        print(infoEjido['OBSERVACIONES'])
    return True
        
@RegisterFunction("info", "Info", "INFO", "infoejido", "INFOEJIDO")
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
                continue
                print(f" > {key}: .." + "\\" + value.split('\\')[-2] + "\\" + value.split('\\')[-1])
            else:
                print(f' > {key}: {value}')

@RegisterFunction("recargarinfoejidos", "RECARGARINFOEJIDOS")
def RecargarInfoEjidos():
    """
    Llena el diccionario con las capas de todos los ejidos.
    """
    CompletarDicEjidos(True)










