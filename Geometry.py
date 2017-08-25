#!/usr/bin/env python

#from scipy.spatial import ConvexHull  # Podria no usarse.

"""convexhull.py

Calculate the convex hull of a set of n 2D-points in O(n log n) time.  
Taken from Berg et al., Computational Geometry, Springer-Verlag, 1997.
Prints output as EPS file.

When run from the command line it generates a random set of points
inside a square of given length and finds the convex hull for those,
printing the result as an EPS file.

Usage:

    convexhull.py <numPoints> <squareLength> <outFile>

Dinu C. Gherman
"""


import sys, string, random


### HELPERS ####

def _myDet(p, q, r):
    """Calc. determinant of a special matrix with three 2D points.

    The sign, "-" or "+", determines the side, right or left,
    respectivly, on which the point r lies, when measured against
    a directed vector from p to q.
    """

    # We use Sarrus' Rule to calculate the determinant.
    # (could also use the Numeric package...)
    sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
    sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

    return sum1 - sum2


def _isRightTurn((p, q, r)):
    "Do the vectors pq:qr form a right turn, or not?"

    assert p != q and q != r and p != r
            
    if _myDet(p, q, r) < 0:
        return 1
    else:
        return 0


def _isPointInPolygon(r, P):
    "Is point r inside a given polygon P?"

    # We assume the polygon is a list of points, listed clockwise!
    for i in xrange(len(P[:-1])):
        p, q = P[i], P[i+1]
        if not _isRightTurn((p, q, r)):
            return 0 # Out!        

    return 1 # It's within!


def _makeRandomData(numPoints=10, sqrLength=100, addCornerPoints=0):
    "Generate a list of random points within a square."
    
    # Fill a square with random points.
    min, max = 0, sqrLength
    P = []
    for i in xrange(numPoints):
        rand = random.randint
        x = rand(min+1, max-1)
        y = rand(min+1, max-1)
        P.append((x, y))
    # Add some "outmost" corner points.
    if addCornerPoints != 0:
        P = P + [(min, min), (max, max), (min, max), (max, min)]
    return P
######################################################################
# Output
######################################################################

epsHeader = """%%!PS-Adobe-2.0 EPSF-2.0
%%%%BoundingBox: %d %d %d %d

/r 2 def                %% radius

/circle                 %% circle, x, y, r --> -
{
    0 360 arc           %% draw circle
} def

/cross                  %% cross, x, y --> -
{
    0 360 arc           %% draw cross hair
} def

1 setlinewidth          %% thin line
newpath                 %% open page
0 setgray               %% black color

"""

def saveAsEps(P, H, boxSize, path):
    "Save some points and their convex hull into an EPS file."
    
    # Save header.
    f = open(path, 'w')
    f.write(epsHeader % (0, 0, boxSize, boxSize))

    format = "%3d %3d"

    # Save the convex hull as a connected path.
    if H:
        f.write("%s moveto\n" % format % H[0])
        for p in H:
            f.write("%s lineto\n" % format % p)
        f.write("%s lineto\n" % format % H[0])
        f.write("stroke\n\n")

    # Save the whole list of points as individual dots.
    for p in P:
        f.write("%s r circle\n" % format % p)
        f.write("stroke\n")
            
    # Save footer.
    f.write("\nshowpage\n")


######################################################################
# Public interface
######################################################################


def convexHull_DEPRECATED(P):
    "Calculate the convex hull of a set of points."

    # Get a local list copy of the points and sort them lexically.
    points = map(None, P)
    points.sort()

    # Build upper half of the hull.
    upper = [points[0], points[1]]
    for p in points[2:]:
        upper.append(p)
        while len(upper) > 2 and not _isRightTurn(upper[-3:]):
            del upper[-2]

    # Build lower half of the hull.
    points.reverse()
    lower = [points[0], points[1]]
    for p in points[2:]:
        lower.append(p)
        while len(lower) > 2 and not _isRightTurn(lower[-3:]):
            del lower[-2]

    # Remove duplicates.
    del lower[0]
    del lower[-1]

    # Concatenate both halfs and return.
    return tuple(upper + lower)


### OTRO INTENTO
# Fuente: Wikipedia.
def convexHull_Wikipedia(points):
    """Computes the convex hull of a set of 2D points.
 
    Input: an iterable sequence of (x, y) pairs representing the points.
    Output: a list of vertices of the convex hull in counter-clockwise order,
      starting from the vertex with the lexicographically smallest coordinates.
    Implements Andrew's monotone chain algorithm. O(n log n) complexity.
    """
 
    # Sort the points lexicographically (tuples are compared lexicographically).
    # Remove duplicates to detect the case we have just one unique point.
    points = sorted(set(points))
 
    # Boring case: no points or a single point, possibly repeated multiple times.
    if len(points) <= 1:
        return points
 
    # 2D cross product of OA and OB vectors, i.e. z-component of their 3D cross product.
    # Returns a positive value, if OAB makes a counter-clockwise turn,
    # negative for clockwise turn, and zero if the points are collinear.
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
 
    # Build lower hull 
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
 
    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
 
    # Concatenation of the lower and upper hulls gives the convex hull.
    # Last point of each list is omitted because it is repeated at the beginning of the other list. 
    return lower[:-1] + upper[:-1]


def convexHull_SimPy(points):
    hull = ConvexHull(points)
    puntos = []
    vertices = hull.vertices
    for v in vertices:
        puntos.append(points[v])
    return puntos

# Devuelve un convex hull horrible, con los vertices desordenados.


# A veces el convex hull es de un punto, muy raro.



convexHull = convexHull_Wikipedia



############# 
## AREA DE UN POLIGONO EN LA SUPERFICIE DE LA TIERRA.
#############


def reproject(latitude, longitude):
    """Returns the x & y coordinates in meters using a sinusoidal projection"""
    from math import pi, cos, radians
    earth_radius = 6371009 # in meters
    lat_dist = pi * earth_radius / 180.0

    y = [lat * lat_dist for lat in latitude]
    x = [long * lat_dist * cos(radians(lat)) 
                for lat, long in zip(latitude, longitude)]
    return x, y


def area_of_polygon(x, y):
    """Calculates the area of an arbitrary polygon given its verticies"""
    area = 0.0
    for i in xrange(-1, len(x)-1):
        area += x[i] * (y[i+1] - y[i-1])
    return abs(area) / 2.0


def areaEarthSurface(polygon):
    lats = []
    longs = []
    for p in polygon:
        lats.append(p[0])
        longs.append(p[1])
    x, y = reproject(lats, longs)
    return area_of_polygon(x,y)



######################################################################
# Test
######################################################################

def test():
    a = 200
    p = _makeRandomData(30, a, 0)
    c = convexHull(p)
    saveAsEps(p, c, a, file)


# determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs.

def pointInsidePolygon(x,y,poly):
    n = len(poly)
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside


# Devuelve el extent de contencion de un poligono.
def getExtent(poly):
    lats = []
    longs = []
    for point in poly:
        lats.append(point[0])
        longs.append(point[1])
    minLat = min(lats)
    maxLat = max(lats)
    minLong = min(longs)
    maxLong = max(longs)
    return {'minLat': minLat, 'maxLat': maxLat, 'minLong': minLong, 'maxLong': maxLong}

def pointInExtent(x,y, extent):
    #print "x,y" + str(x) + "," + str(y)
    #print "Extent: " + str(extent) 
    return x >= extent['minLat'] and x <= extent['maxLat'] and y >= extent['minLong'] and y <= extent['maxLong']


def preCalcExtents(polis):
    extents = []
    for p in polis:
        extents.append(getExtent(p))
    return extents

# Las municipalidades del shape file tienen invertido el Lat y el Lon, por eso se usa esto.
def invertirLatLon(poligono):
    poligonoNuevo = []
    for punto in poligono:
        poligonoNuevo.append((punto[1], punto[0]))
    return poligonoNuevo


