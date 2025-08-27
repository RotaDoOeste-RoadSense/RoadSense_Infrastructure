import os
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from create_new_trip_id import create_new_trip
from typing import Optional

app = FastAPI()

@app.post("/new-trip/")
async def new_trip(
    path: str = Form(None),
    way: Optional[str] = Form(None),
    starting_city: Optional[str] = Form(None),
    ending_city: Optional[str] = Form(None),
    prod: bool = Form(False),
):
    response_content = create_new_trip(
        root_folder=path,
        way=way,
        starting_city=starting_city,
        ending_city=ending_city,
        prod = prod
    )
    return JSONResponse(content = response_content
        
    )





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
