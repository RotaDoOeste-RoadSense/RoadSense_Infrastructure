from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

def nearest_polyline(lat, lng, polylines):
    point = Point(lat, lng)
    point_min_distance = None
    nearest_id = None
    min_distance = float('inf')
    for id, line in polylines.items():
        # Find the nearest point on the line
        nearest_point = nearest_points(point, line)
        nearest_point = nearest_point[1]

        distance = point.distance(nearest_point)
        if distance < min_distance:
            min_distance = distance
            nearest_id = id
            point_min_distance = nearest_point
    
    return min_distance, point_min_distance, nearest_id
