from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from core.utils import get_segment_km

app = FastAPI()

@app.get("/get_segment_km")
@version(1, 0)
async def get_segment_km_api(trip_id: int = Query(...), lat: float = Query(...), lon: float = Query(...)):
    try:
        coordinate = (lat, lon)
        segment_km = get_segment_km(trip_id, coordinate)
        return JSONResponse(content={'closest': segment_km[0], 'second_closest': segment_km[1]})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(app, enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)
