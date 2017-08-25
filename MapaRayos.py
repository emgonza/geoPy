

import shapefile
import fiona
import pyproj 
from shapely.ops import transform
from shapely.geometry import shape, mapping, Point
from functools import partial

from Geometry import *

# ES MUY INCOMODA ESTA LIBRERIA...

# Ejemplo 1, apertura de un shapefile y visualizacion de campos.
def mostrarShapefile():
    sf = shapefile.Reader("municipios/Sudamerica_adm2_simpl")
    shapes = sf.shapes()
    print "Hay ", len(shapes), " shapes en el archivo."
    print "Campos: ", sf.fields
    records = sf.records()
    print "Hay ", len(records), " registros."
    # Lectura simultanea de ambos.
    shapeRecs = sf.shapeRecords()
    print "Registro 0: ", shapeRecs[0].record
    print "Registro 14: ", shapeRecs[13].record
    print "Shape 0: ", shapeRecs[0].shape
    print "Points 0: ", shapeRecs[0].shape.points
    print "Parts: ", shapeRecs[0].shape.parts


#  Ejemplo 2, abrimos el shapefile y filtramos aquellos registros que son de paises.
#def filterCountries():
#    sf = shapefile.Reader("municipios/Sudamerica_adm2_simpl")
#    shapeRecs = sf.shapeRecords()
#    w = shapefile.Writer()


def levantarRayos(archivo):
    f = open(archivo)
    linea = f.readline() # Salteamos encabezado
    linea = f.readline() 
    rayos = []
    while linea != "":
        tokens = linea.split(",")
        rayos.append({"lat": float(tokens[2]), "lon": float(tokens[3])})
        linea = f.readline()
    f.close()
    return rayos


def partirLista(lista, partsIndex):
    partes = []
    for i in range(len(partsIndex)-1):
        partes.append(lista[partsIndex[i]:partsIndex[i+1]])
    partes.append(lista[partsIndex[len(partsIndex)-1]:])    
    return partes


def cargarRayosShapefile(archivoShape, archivoRayos, archivoSalida):
    rayos = levantarRayos(archivoRayos)
    # Levantamos el shapefile de inicio.
    r = shapefile.Reader(archivoShape)
    shapeRecs = r.shapeRecords()
    # Prepreoceso, cargamos los extents de cada "municipio".
    w = shapefile.Writer(r.shapeType) # Ver si esta bien el tipo. shapefile.POLYGON
    #w.fields =list(sf.fields)
    #w.field('Area', 'N', 18, 5)
    #w.field('Rayos', 'N', 10,0)
    #w.field('Densidad', 'N', 18,5)
    municipios = []
    index = 0
    for shr in shapeRecs:
        #if index >= 100:
        #    for i in range(100, len(shapeRecs)):
        #        municipios.append({"area": 0.0, "rayos": 0, "densidad": 0.0})
        #    break
        print "Procesando feature ", index
        index += 1
        shape = shr.shape
        record = shr.record
        cantidadRayos = 0
        # Salteamos si el record corresponde a un pais y no a un departamento.
        if record[2] != '':
            continue
        shapePoints = invertirLatLon(shape.points)
        shapeParts = shape.parts
        poligonos = partirLista(shapePoints, shapeParts)
        areaTotalDepto = 0.0
        parts = []
        for poligono in poligonos:
            areaTotalDepto = areaTotalDepto + areaEarthSurface(poligono)/ (1000.0*1000.0)  # Area en Km2.
            extent = getExtent(poligono)
            # Recorremos los rayos.
            for rayo in rayos:
                latitud = rayo["lat"]
                longitud = rayo["lon"]
                if pointInExtent(latitud, longitud, extent) and pointInsidePolygon(latitud, longitud, poligono):
                    cantidadRayos = cantidadRayos + 1
        densidadRayos = float(cantidadRayos) / areaTotalDepto
        municipios.append({"area": areaTotalDepto, "rayos": cantidadRayos, "densidad": densidadRayos})
        # Generamos el nuevo registro.
        # Primero la geometria.
        #if len(shape.parts)==1:
    #w.fields = list(r.fields)
    w._shapes = r.shapes()
    #records = r.records()
    w.field('Area', 'N', 18, 5)
    w.field('Rayos', 'N', 10,0)
    w.field('Densidad', 'N', 18,5)
    for municipio in municipios:
        w.record(municipio["area"], municipio["rayos"], municipio["densidad"])
    w.save(archivoSalida)




def testLevantarRayos():
    rayos = levantarRayos("./datos/A20150101.loc")
    print "Se levantaron ", len(rayos), " rayos."

############################################ FIONA ##########################

def fionaMostrarShapefile():
    c = fiona.open('municipios/Sudamerica_adm2_simpl.shp', 'r')
    features = list(c)
    print "Hay ", len(features), " geometrias."
    print "Feature 430: ", features[430]
    #print "Feature 2:" , features[2]
    w = fiona.open('municipios/Geometria430', 'w', driver = c.driver,
        crs = c.crs, # Proyeccion.
        schema = c.schema) # Esquema de la geometria y la proyeccion.
    rec = features[430]
    w.write(rec)
    w.close()

def generarNuevoShapefile():
    c = fiona.open('municipios/Sudamerica_adm2_simpl.shp', 'r')
    features = list(c)
    print "Hay ", len(features), " geometrias."
    #print "Geometria 430: ", geometrias[430]
    nuevoSchema = c.schema['properties']['area'] = 'float:19.11'
    nuevoSchema = c.schema['properties']['rayos'] = 'int:12'
    nuevoSchema = c.schema['properties']['densidadRayos'] = 'float:19.11'
    w = fiona.open('municipios/GeometriaRayos', 'w', driver = c.driver,
        crs = c.crs, # Proyeccion.
        schema = c.schema) # Esquema de la geometria y la proyeccion.
    print "Schema: ", c.schema
    contador = 0
    proj = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'),
           pyproj.Proj(init='epsg:3857'))
    rayos = levantarRayos("./datos/A20150101.loc")
    for feature in features:
        if feature["properties"]["NAME_ENGLI"] == None:
            continue
        if contador % 1 == 0:
            print "Procesando feature ", contador
        contador += 1
        #feature['properties']['area'] = shape(feature["geometry"]).area # Es un area euclidiana, es incorrecta.
        geometria = feature['geometry']
        s = shape(geometria)
        s_new = transform(proj, s)
        projected_area = transform(proj, s).area
        feature['properties']['area'] = projected_area
        cantRayos = 0
        indexRayo = 0
        rayosEliminar = 0
        for rayo in rayos:
            punto = Point(rayo["lon"], rayo["lat"])
            if s.contains(punto):
                cantRayos += 1
            indexRayo += 1
        feature['properties']['rayos'] = cantRayos
        feature['properties']['densidadRayos'] = float(cantRayos) / projected_area
        w.write(feature)
    c.close()
    w.close() 


def bboxContainsPoint(bbox, x, y):
    if x < bbox[0]:
        return False
    if x > bbox[2]:
        return False
    if y < bbox[1]:
        return False
    if y > bbox[3]:
        return False
    return True

def generarNuevoShapefileImproved():
    c = fiona.open('municipios/Sudamerica_adm2_simpl.shp', 'r')
    features = list(c)
    print "Hay ", len(features), " geometrias."
    #print "Geometria 430: ", geometrias[430]
    nuevoSchema = c.schema['properties']['area'] = 'float:19.11'
    nuevoSchema = c.schema['properties']['rayos'] = 'int:12'
    nuevoSchema = c.schema['properties']['densidadRayos'] = 'float:19.11'
    w = fiona.open('municipios/GeometriaRayos', 'w', driver = c.driver,
        crs = c.crs, # Proyeccion.
        schema = c.schema) # Esquema de la geometria y la proyeccion.
    print "Schema: ", c.schema
    contador = 0
    proj = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'),
           pyproj.Proj(init='epsg:3857'))
    rayos = levantarRayos("./datos/A20150101.loc")
    # Precalculo de bounding box.
    print "Preprocesando municipios..."
    municipios = []
    contador = 0
    for feature in features:
        if contador % 50 == 0:
            print "Procesando feature ", contador
        contador += 1
        # Salteamos los paises.
        if feature["properties"]["NAME_ENGLI"] != None:
            continue
        municipio = {}
        municipios.append(municipio)
        municipio['feature'] = feature
        s = shape(feature['geometry'])
        s_new = transform(proj, s)
        projected_area = transform(proj, s).area
        municipio['rayos'] = 0
        municipio['shape'] = s
        municipio['bbox'] = s.bounds
        municipio['area'] = projected_area
    print "Procesando rayos"
    contador = 0
    for rayo in rayos:
        if contador % 100 == 0:
            print "Procesando rayo ", contador
        contador += 1
        # Si esta fuera de sudamerica, saltar.
        if rayo["lon"] < -90.0 or rayo["lon"] > -28.0:
            continue
        if rayo["lat"] < -57.0 or rayo["lat"] > 14.0:
            continue 
        if contador > 1000:
            break
        for municipio in municipios:
            s = municipio['shape']
            bbox = municipio['bbox']
            feature['properties']['area'] = projected_area
            punto = Point(rayo["lon"], rayo["lat"])
            if bboxContainsPoint(bbox,rayo["lon"], rayo["lat"]) and s.contains(punto):
            #if s.contains(punto):
                municipio['rayos'] = municipio['rayos'] + 1
                break
    print "Posprocesamiento..."
    for municipio in municipios:
        feature = municipio['feature']
        feature['properties']['rayos'] = municipio['rayos']
        feature['properties']['area'] = municipio['area']
        feature['properties']['densidadRayos'] = float(municipio['rayos'])/municipio['area']
        w.write(feature)
    c.close()
    w.close() 


#mostrarShapefile()
#testLevantarRayos()
#cargarRayosShapefile("municipios/Sudamerica_adm2_simpl", "./datos/A20150101.loc", 
#    "municipios/Rayos")

#fionaMostrarShapefile()
#generarNuevoShapefile()
generarNuevoShapefileImproved()