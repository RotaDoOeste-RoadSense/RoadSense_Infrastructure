from .database import Session, PlacaKm, PlateDetails, AllPlatesMatched, ImageData
from .geosearch import GeodesicBinarySearch

from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_placas_km_by_trip(trip_id):
    session = Session()
    try:
        results = session.query(
            PlacaKm.km_plate_id,
            PlacaKm.km,
            PlacaKm.BR,
            ImageData.latitude,
            ImageData.longitude
        ).join(PlateDetails, PlacaKm.km_plate_id == PlateDetails.plate_details_id).join(AllPlatesMatched, PlateDetails.image_id == AllPlatesMatched.all_plates_matched_id).join(
            ImageData, AllPlatesMatched.image_id == ImageData.image_id
        ).filter(
            ImageData.trip_id == trip_id
        ).order_by(PlacaKm.km_plate_id).all()

        return results
    finally:
        session.close()

def get_segment_km(trip_id, coordinate):
    results = fetch_placas_km_by_trip(trip_id)
    geosearch = GeodesicBinarySearch([tuple(_[-2:]) for _ in results], [_[:3] for _ in results])
    return geosearch.search_optimized(coordinate)
