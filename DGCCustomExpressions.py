"""
Custom expressions for use in the field calculator. Automatically loaded on startup of DGC's qgz files. Docstrings, comments,etc are pending, I made this when I had not a clue about what to do or how.
"""

import qgis
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from CommonFunctions import *

@qgsfunction(args='auto', group='DGC-Custom')
def STR_EtiquetaMzna(parcela):
    """
    Devuelve la etiqueta de manzana/quinta/chacra de la entidad.
    """
    nomenclatura = CalcularNomenclatura(parcela)
    etiqueta = nomenclatura.split('-')[-1]
    return etiqueta

@qgsfunction(args='auto', group='DGC-Custom')
def GEOM_NormalizarPrimerVertice(geometria):
    """
    Recibe una geometria de poligono, la devuelve con el primer vertice siendo aquel mas al oeste. En caso de conflicto, prioriza aquel mas al sur.
    """
    return GEOM_NormalizeFirstVertex(geometria)

@qgsfunction(args='auto', group='DGC-Custom')
def STR_DesagregarMedida(entidad, indiceLinea, campo='MEDIDAS', separador='-'):
    """
    Recibe una entidad y un indice de linea. Devuelve la etiqueta de medida singular para ese indice.
    """
    default = f'<{indiceLinea}>'
    medidas = entidad[campo] if entidad[campo] is not None else ''
    if not medidas:
        return default
    listaMedidas = medidas.split(separador)
    if len(listaMedidas) < indiceLinea:
        return default
    else:
        return listaMedidas[indiceLinea-1]

@qgsfunction(args='auto', group='DGC-Custom')
def STR_CiclarCadena(cadena, separador='-'):
    """
    Recibe una cadena, la trata como una lista usando separador='-', y la devuelve con el primer item pasado al ultimo lugar.
    """
    lista = cadena.split(separador)
    lista = lista[1:] + [lista[0]]
    nuevaCadena = '-'.join(lista)
    return nuevaCadena

@qgsfunction(args='auto', group='DGC-Custom')
def RGB_ColorRegistrado(registrado, pastel=True):
    regs = (reg for reg in str(registrado).split('-'))
    reg = max(regs)
    suma = 0
    for n in reg:
        if n.isdigit():
            suma += int(n)
        if suma > 25:
            suma -= 25
    color = f"REG{suma} PASTEL" if pastel else f"REG{suma}"
    return color

@qgsfunction(args='auto', group='DGC-Custom')
def RGB_VerificarMedida(
        entidad, 
        indiceLinea, 
        longLinea, 
        separador='-', 
        toleranciaMin=0.01, 
        toleranciaMax=0.05,
        nombreCampo='MEDIDAS'):
    """
    Compara la longitud real de la linea en un indice del poligono, con la etiqueta de la misma. Devuelve colores segun que tanta diferencia haya entre ellas.
    """
    colorMuchaDiferencia = '#FF0000'
    colorPocaDiferencia = '#FFAA00'
    colorOK = '#000000'
    medidas = entidad[nombreCampo] if entidad[nombreCampo] is not None else ''
    if not medidas:
        return colorMuchaDiferencia
    listaMedidas = medidas.split(separador)
    try:
        etiqueta = float(listaMedidas[indiceLinea-1])
    except:
        return colorMuchaDiferencia
    if longLinea > etiqueta*(1+toleranciaMax) or longLinea < etiqueta*(1-toleranciaMax):
        return colorMuchaDiferencia
    if longLinea > etiqueta*(1+toleranciaMin) or longLinea < etiqueta*(1-toleranciaMin):
        return colorPocaDiferencia
    return colorOK

#################BARRA SEPARADORA DE BAJO PRESUPUESTO###############################
#De aca para abajo son todas funciones viejas
@qgsfunction(args='auto', group='Custom')
def CC123(cc, feature, parent):
    if cc == 1:
        return 1
    if cc == 2 or cc == 5:
        return 2
    if cc == 3 or cc==4:
        return 3
    return 0

@qgsfunction(args='auto', group='Custom')
def DatosEjidos(ejido, dato, feature, parent):
    dicEjidos={
        #EJIDO:NOMBRE,FAJA
        1:['Realicó',4],
        2:['A. Van Praet',4],
        3:['Ojeda',4],
        4:['Alta Italia',4],
        5:['Embajador Martini',4],
        6:['Ingeniero Luiggi',4],
        7:['Maisonnave',4],
        8:['',4],
        9:['Falucho',4],
        10:['Hilario Lagos',4],
        11:['',4],
        12:['Sarah',4],
        13:['Bernardo Larroudé',4],
        14:['Vertiz',4],
        15:['Intendente Alvear',4],
        16:['Ceballos',4],
        17:['Speluzzi',4],
        18:['Agustoni',4],
        19:['Dorila',4],
        20:['Trebolares',4],
        21:['General Pico',4],
        22:['Arata',4],
        23:['Metileo',4],
        24:['Monte Nievas',4],
        25:['Trenel',4],
        26:['Eduardo Castex',4],
        27:['Mauricio Mayer',4],
        28:['Winifreda',4],
        29:['Bouef',4],
        30:['',4],
        31:['',4],
        32:['Relmo',4],
        33:['Colonia San Jose',4],
        34:['Quemú Quemú',4],
        35:['Miguel Cané',4],
        36:['Colonia Barón',4],
        37:['Villa Mirasol',4],
        38:['Huelen',4],
        39:['Catriló',4],
        40:['',4],
        41:['Uriburu',4],
        42:['Lonquimay',4],
        43:['La Gloria',4],
        44:['Anguil',4],
        45:['Cachirulo',4],
        46:['Toay',4],
        47:['Santa Rosa',4],
        48:['Naicó',4],
        49:['Doblas',4],
        50:['Quehue',4],
        51:['Ataliva Roca',4],
        52:['',4],
        53:['Rolón',4],
        54:['Miguel Riglos',4],
        55:['Tomas M. Anchorena',4],
        56:['Hidalgo',4],
        57:['',4],
        58:['Macachín',4],
        59:['Colonia Santa Teresa',4],
        60:['Guatraché',4],
        61:['',4],
        62:['Alpachiri',4],
        63:['',4],
        64:['General Campos',4],
        65:['Perú',4],
        66:['',4],
        67:['Colonia Santa Maria',4],
        68:['',4],
        69:['Unanue',4],
        70:['',4],
        71:['Hucal',4],
        72:['Jacinto Arauz',4],
        73:['Abramo',4],
        74:['San Martín',4],
        75:['Bernasconi',4],
        76:['La Adela',4],
        77:['',3],
        78:['',3],
        79:['Chamaicó',3],
        80:['Rancul',3],
        81:['Quetrequén',3],
        82:['Parera',3],
        83:['Caleufú',3],
        84:['La Maruja',3],
        85:['Pichi Huinca',3],
        86:['Ingeniero Foster',3],
        87:['Luan Toro',3],
        88:['Telen',3],
        89:['Victorica',3],
        90:['Loventue',3],
        91:['Conhello',3],
        92:['',3],
        93:['Ceriola',3],
        94:['Rucanelo',3],
        95:['Carro Quemado',3],
        96:['',3],
        97:['General Acha',3],
        98:['Chacharramendi',3],
        99:['Cuchillo Có',3],
        100:['',3],
        101:['',3],
        102:['Puelches',3],
        103:['Santa Isabel',3],
        104:['',3],
        105:['',3],
        106:['',3],
        107:['Limay Mahuida',3],
        108:['La Reforma',3],
        109:['Algarrobo Del Aguila',3],
        110:['Puelen',2],
        111:['',2],
        112:['Colonia 25 De Mayo',2],
        113:['',2],
        114:['Gobernador Dubal',2],
        115:['LaHumada',2],
        116:['Colonia Chica',2],
        117:['Casa De Piedra',2]
    }
    try:
        ejido = int(ejido)
        ejido = dicEjidos[ejido]
        if dato.lower() == 'nombre':
            return ejido[0]
        elif dato.lower() == 'faja':
            return ejido[1]
        else:
            return ['',0]
    except:
        return ['',0]
    
@qgsfunction(args='auto', group='Custom')
def SelectCCColor(cc, feature, parent):
    ccColorDict={
        0:['Otros',255,252,178,'#FFFCB2'],
        1:['Chacras',178,214,255,'#B2D6FF'], 
        2:['Quintas',255,166,166,'#FFA6A6'], 
        3:['Manzanas',152,255,152,'#98FF98'], 
        4:['PHMZ',136,229,136,'#88E588'],
        4:['PHQT',229,149,149,'#E59595'], 
        }
    if cc==4 or cc== 3 or cc==2 or cc==1:
        return ccColorDict[cc][1:]
    else:
        return ccColorDict[0][1:]
        
@qgsfunction(args='auto', group='Custom')
def SeleccionarColor(color, feature, parent):
    ##Por alguna razon, el color 18 no funciona.
    color=int(color)
    rgbColorDict={
        0:['Negro',             0,      0,      0,      '#000000'],
        1:['Lima',              164,    196,    0,      '#A4C400'],
        2:['Cyan',              27,     161,    226,    '#1BA1E2'],
        3:['Rosa',              244,    114,    208,    '#F472D0'],
        4:['Naranja',           250,    104,    0,      '#FA6800'],
        5:['Oliva',             109,    135,    100,    '#6D8764'],
        6:['Verde',             96,     169,    23,     '#60A917'],
        7:['Cobalto',           0,      80,     239,    '#0050EF'],
        8:['Magenta',           216,    0,      115,    '#D80073'],
        9:['Ambar',             240,    163,    10,     '#F0A30A'],
        10:['Acero',            100,    118,    135,    '#647687'],
        11:['Esmeralda',        0,      138,    0,      '#008A00'],
        12:['Indigo',           106,    0,      255,    '#6A00FF'],
        13:['Carmesi',          162,    0,      37,     '#A20025'],
        14:['Amarillo',         227,    200,    0,      '#E3C800'],
        15:['Malva',            118,    96,     138,    '#76608A'],
        16:['Aguamarina',       0,      171,    169,    '#00ABA9'],
        17:['Violeta',          170,    0,      255,    '#AA00FF'],
        18:['RosaClaro',        254,    152,    229,    '#FE98E5'],
        19:['Marron',           130,    90,     44,     '#825A2C'],
        20:['Gris Pardo',       135,    121,    78,     '#87794E'], 
        21:['Cyan Oscuro',      20,     240,    240,    '#14F0F0'], 
        22:['Violeta Oscuro',   75,     0,      130,    '#4B0082'], 
        23:['Rojo Oscuro',      128,    0,      0,      '#800000'], 
        24:['Amarillo Oscuro',  128,    128,    0,      '#808000'], 
        25:['Gris Oscuro',      85,     85,     85,     '#555555']
        }
    aux=color
    while aux>25:
        aux=aux-25
    return rgbColorDict[aux][1:]
    
@qgsfunction(args='auto', group='Custom')
def currentExtent(feature, parent):
    return QgsGeometry.fromRect(iface.mapCanvas().extent())
    
@qgsfunction(args='auto', group='Custom')
def CountChar(word, char, feature, parent):
    return word.count(char)

@qgsfunction(args='auto', group='Custom')   #   CalcRegistrado("TEN","REGISTRADO")
def NomenclaMZNA(ejido,circ,radio,cc,mzna, feature, parent):
    def _Quitar0(asd):      #       Quitar0("MZNA")
        while asd[0] == '0':
            asd = asd[1:]
        return asd
    def _Poner0(tx, chars):
        tx = str(tx)
        if '0123456789'.find(tx[-1]) == -1:
            suffix = tx[-1]
            num = tx[0:-1]
        else:
            suffix = ''
            num = tx
        while len(num) < chars:
            num = '0' + num
        tx = num + suffix
        return tx.upper()
    def _IntToRoman(value):
        value = int(value)
        RomanList = {1: 'I',2: 'II',3: 'III',4: 'IV',5: 'V',
        6: 'VI',7: 'VII',8: 'VIII',9: 'IX',10: 'X',
        11: 'XI',12: 'XII',13: 'XIII',14: 'XIV',15: 'XV',
        16: 'XVI',17: 'XVII',18: 'XVIII',19: 'XIX',20: 'XX',
        21: 'XXI', 22: 'XXII', 23: 'XXIII', 24: 'XXIV', 25: 'XXV'}
        try:
            return RomanList[value]
        except:
            return '?'
    #ejido = Poner0(obj["EJIDO"],3)
    ejido = _Poner0(ejido,3)
    #circ = IntToRoman(obj["CIRC"])
    circ = _IntToRoman(circ)
    #radio = obj["RADIO"].upper()
    #mzna = Quitar0(obj["MZNA"])
    mzna = _Quitar0(mzna)
    #cc = obj["CC"]
    nom = ejido + '-' + circ
    if cc == 1:
        nom = nom + '-Ch.'
    elif cc == 2:
        nom = nom + '-' + radio.upper() + '-Qta.'
    else:
        nom = nom + '-' + radio.upper() + '-Mz.'
    nom = nom + mzna
    return nom

@qgsfunction(args='auto', group='Custom')   #   CalcRegistrado("TEN","REGISTRADO")
def CalcRegistrado(tenencia, regs, feature, parent):
    if not regs:
        return regs
    else:
        etiqueta = regs.strip()
        while etiqueta[-1]=='-':
            etiqueta = etiqueta[0:-1]
        if not etiqueta == '':
            etiqueta = etiqueta.split('-')[-1]
        if tenencia == 'S':
            return 'Inic. ' + etiqueta
        else:
            return 'Reg. ' + etiqueta
            
@qgsfunction(args='auto', group='Custom')   #   CalcRegistrado("TEN","REGISTRADO")
def CalcRegistradoSinTexto(regs, feature, parent):
    if not regs:
        return regs
    else:
        etiqueta = regs.strip()
        while etiqueta[-1]=='-':
            etiqueta = etiqueta[0:-1]
        if not etiqueta == '':
            etiqueta = etiqueta.split('-')[-1]
        return etiqueta
            
@qgsfunction(args='auto', group='Custom')   #   CalcRegistrado("TEN","REGISTRADO")
def DirUltimoRegistrado(regs, feature, parent):
    if not regs:
        return regs
    else:
        etiqueta = regs.strip()
        while etiqueta[-1]=='-':
            etiqueta = etiqueta[0:-1]
        if not etiqueta == '':
            etiqueta = etiqueta.split('-')[-1]
        dir = 'L:/Geodesia/Registrados/'
        if len(etiqueta) == 5:
            dir = dir + etiqueta[0] + etiqueta[1] + '.000/' +  etiqueta[0] + etiqueta[1] + '.' + etiqueta[2] + '00/'
        elif len(etiqueta) == 4:
            dir = dir + '0' + etiqueta[0] + '.000/' +  '0' + etiqueta[0] + '.' + etiqueta[1] + '00/'
        elif len(etiqueta) == 3:
            dir = dir + '00.000/00.' + etiqueta[1] + '00/'
        else:
            dir = dir + '00.000/00.000/'
        etiqueta = str(Poner0(etiqueta,5))
        dir = dir + etiqueta[0] + etiqueta[1] + '.' + etiqueta[2:] + '.pdf'
        return dir
            
@qgsfunction(args='auto', group='Custom')
def GetNomFromMzQtCh(obj, feature, parent):
    nom = str(obj['EJIDO']) + '-' + str(obj['CIRC']) + '-' + obj['RADIO'] + '-' + str(obj['CC']) + '-' + obj['MZNA']
    return nom

@qgsfunction(args='auto', group='Custom')
def IntToRoman(value, feature, parent):
    try:
        value = int(value)
    except:
        return value
    RomanList = {1: 'I',2: 'II',3: 'III',4: 'IV',5: 'V',
    6: 'VI',7: 'VII',8: 'VIII',9: 'IX',10: 'X',
    11: 'XI',12: 'XII',13: 'XIII',14: 'XIV',15: 'XV',
    16: 'XVI',17: 'XVII',18: 'XVIII',19: 'XIX',20: 'XX',
    21: 'XXI', 22: 'XXII', 23: 'XXIII', 24: 'XXIV', 25: 'XXV'}
    try:
        return RomanList[value]
    except:
        return '?'

@qgsfunction(args='auto', group='Custom')
def RomanToInt(value, feature, parent):
    RomanList = {1: 'I',2: 'II',3: 'III',4: 'IV',5: 'V',
    6: 'VI',7: 'VII',8: 'VIII',9: 'IX',10: 'X',
    11: 'XI',12: 'XII',13: 'XIII',14: 'XIV',15: 'XV',
    16: 'XVI',17: 'XVII',18: 'XVIII',19: 'XIX',20: 'XX',
    21: 'XXI', 22: 'XXII', 23: 'XXIII', 24: 'XXIV', 25: 'XXV'}
    for n in range(1,50):
        try:
            if RomanList[n] == value:
                return n
        except:
            return 0
    else:
        return 0
        
@qgsfunction(args='auto', group='Custom')
def Quitar0(asd, feature, parent):      #       Quitar0("MZNA")
    if asd[0].upper() == 'X':
        asd = asd[1:]
    while asd[0] == '0':
        asd = asd[1:]
    if asd[-1].upper() == 'X':
        asd = asd[:-1]
    return asd
    
@qgsfunction(args='auto', group='Custom')
def Poner0(tx, chars, feature, parent):
    tx = str(tx)
    if '0123456789'.find(tx[-1]) == -1:
        suffix = tx[-1]
        num = tx[0:-1]
    else:
        suffix = ''
        num = tx
    while len(num) < chars:
        num = '0' + num
    tx = num + suffix
    return tx.upper()

@qgsfunction(args='auto', group='Custom')
def Poner0Decimal(tx, num, feature, parent):
    tx=str(tx)
    try:
        tx.index('.')
        tx = str(tx).partition('.')
    except:
        try:
            tx.index(',')
            tx = str(tx).partition(',')
        except:
            return tx
    while len(tx[2]) < num:
        tx = [tx[0], tx[1],tx[2] + '0']
    if tx[2]=='00':
        return tx[0]
    else:
        return tx[0] + tx[1] + tx[2]
    
@qgsfunction(args='auto', group='Custom')
def IntToPrefix(cc, feature, parent):
    if int(cc) == 3:
        return 'Mz.'
    elif int(cc) == 2:
        return 'Qta.'
    elif  int(cc) == 1:
        return 'Ch.'
    else:
        return '?.'

@qgsfunction(args='auto', group='Custom')
def formatearParamMzna(tx, feature, parent):
    def Poner0(tx, chars):
        if '0123456789'.find(tx[-1]) == -1:
            suffix = tx[-1]
            num = tx[0:-1]
        else:
            suffix = ''
            num = tx
        while len(num) < chars:
            num = '0' + num
        tx = num + suffix
        return tx.upper()
        
    def IntToRoman(value):
        value = int(value)
        RomanList = {1: 'I',2: 'II',3: 'III',4: 'IV',5: 'V',
        6: 'VI',7: 'VII',8: 'VIII',9: 'IX',10: 'X',
        11: 'XI',12: 'XII',13: 'XIII',14: 'XIV',15: 'XV',
        16: 'XVI',17: 'XVII',18: 'XVIII',19: 'XIX',20: 'XX',
        21: 'XXI', 22: 'XXII', 23: 'XXIII', 24: 'XXIV', 25: 'XXV'}
        try:
            return RomanList[value]
        except:
            return '?'
    #EJIDO Y CIRC
    ejido = Poner0 (tx.split('.')[0], 3)
    circ = IntToRoman (tx.split('.')[1])
    nom = ejido + '-' + circ + '-'
    #RADIO
    if tx.split('.')[2] == '-':
        nom = nom
    else:
        nom = nom + tx.split('.')[2].upper() + '-'
    #CC
    if int(tx.split('.')[3]) == 3:
        nom = nom + 'Mz.' + tx.split('.')[4]
    elif int(tx.split('.')[3]) == 2:
        nom = nom + 'Qta.' + tx.split('.')[4]
    elif  int(tx.split('.')[3]) == 1:
        nom = nom + 'Ch.' + tx.split('.')[4]
    else:
        nom = nom + tx.split('.')[4]
    return nom
  
@qgsfunction(args='auto', group='Custom')
def SelectPrefixFromCC (CC, feature, parent):
    if CC == 3:
        return 'Mz.'
    elif CC == 2:
        return 'Qta.'
    elif  CC == 1:
        return 'Ch.'
    else:
        return ''
        
@qgsfunction(args='auto', group='Custom')
def SelectIndexFromString(string, sep, index, feature,parent):
    lista = string.split('-')
    return lista[index]

@qgsfunction(args='auto', group='Custom')
def CountChars(string, char, feature,parent):
    num = 0
    for c in string:
        if c == char:
            num = num+1
    return num
    
@qgsfunction(args='auto', group='Custom')
def RegOrdering(regs,feature,parent):
    def Quitar0(tx):
        while tx[0] == '0':
            tx = tx[1:]
        return tx
    def Poner0(tx, chars):
        tx = str(tx)
        if '0123456789'.find(tx[-1]) == -1:
            suffix = tx[-1]
            num = tx[0:-1]
        else:
            suffix = ''
            num = tx
        while len(num) < chars:
            num = '0' + num
        tx = num + suffix
        return tx.upper()
    if regs[0].upper()=='X':
        regs=regs[1:]
    txlist = regs.rsplit('-')
    aux = []
    for item in txlist:
        if int(item)==0:
            aux.append(item)
    for x in aux:
        txlist.remove(x)
    list = []
    for item in txlist:
        list.append(Poner0(item,5))
    list.sort()
    regs=''
    for item in list:
        regs= regs + Quitar0(item) + '-'
    if regs[-1] == '-':
        regs = regs[:-1]
    return regs
    
