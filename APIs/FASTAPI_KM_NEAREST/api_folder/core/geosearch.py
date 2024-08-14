from functools import lru_cache
from geopy.distance import geodesic

@lru_cache(maxsize=128)
def distance(p1, p2):
    return geodesic(p1, p2).meters

class GeodesicBinarySearch:
    def __init__(self, samples, labels) -> None:
        self._samples = samples
        self._labels = labels

    def search_optimized(self, target):
        start, end = 0, len(self._samples) - 1
        closest_idx = start
        while start <= end:
            mid = (start + end) // 2
            dist_mid = distance(target, self._samples[mid])
            dist_closest = distance(target, self._samples[closest_idx])
            if dist_mid < dist_closest:
                closest_idx = mid
            if distance(target, self._samples[start]) < distance(target, self._samples[end]):
                end = mid - 1
            else:
                start = mid + 1
        
        previous_idx = max(0, closest_idx - 1)
        next_idx = min(len(self._samples) - 1, closest_idx + 1)
        dist_prev = distance(target, self._samples[previous_idx])
        dist_next = distance(target, self._samples[next_idx])   
        second_closest_idx = previous_idx if dist_prev < dist_next else next_idx
        return self._labels[closest_idx], self._labels[second_closest_idx],
