'''
MIT License
Author:         Jacob B Fullerton
Date:           August, 2018
Company:        Intera Inc.
Usage:          Intended for internal use at Intera Inc. to generate points for a semi-regular MODFLOW USG grid
Pseudo Code:    The code in general works in the following manner:
                1.  Inputs
                2.  Initialize variables, especially dictionary of points by year
                3.  Using for loop, traverse all years in the selected folder, populating dictionary
                4.  After populating dictionary, export results to STOMP readable boundary condition card
'''
import random, os, pandas
import vectormath as vmath
import numpy as np
from shapely.geometry import Point

# Initialize key variables
# Props to @user13993 and @Nisan.H on stackoverflow.com for this elegant answer. Obtains the working directory of the
# script upon runtime
working_dir = os.path.dirname(os.path.realpath(__file__))
# Origin is located in top-left corner
origin = {'X': 5661358, 'Y': 19628008}
len_x = 8000
len_y = 8000
num_nodes = 1500
min_dist = 160
outfile = 'refinement.txt'

# Input to feed point generating function
v1 = vmath.Vector2(8000, 0)
v2 = vmath.Vector2(0, 8000)

points = pandas.DataFrame()
node = 1
while len(points) < num_nodes:
    a1 = random.random()
    a2 = random.random()
    point = a1 * v1 + a2 * v2
    # Verify that the minimum distance is honored by the new point
    if len(points) == 0:
        points = pandas.DataFrame.from_dict(
            {str(node):
                 [origin['X'] + point.x,
                  origin['Y'] - point.y,
                  Point(point.x, point.y)]
             },
            orient='index', columns=['X', 'Y', 'geometry'])
    else:
        distances = [Point(origin['X'] + point.x, origin['Y'] - point.y).distance(check) for check in points.geometry]
        if any(dist < min_dist for dist in distances):
            continue
    # Add X origin to x-coordinate and subtract y-coordinate from Y origin
    points = points.append(pandas.DataFrame.from_dict(
        {str(node):
             [origin['X'] + point.x,
              origin['Y'] - point.y,
              Point(origin['X'] + point.x, origin['Y'] - point.y)]
         },
        orient='index', columns=['X','Y', 'geometry']), sort=True)
    node += 1
    print("Number of acceptable nodes = " + str(len(points)))
points.to_csv(path_or_buf=os.path.join(working_dir, outfile),columns=['X','Y'])