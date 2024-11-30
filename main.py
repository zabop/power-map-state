from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from xml.etree import ElementTree as ET
import geopandas as gpd
import shapely.geometry
import urllib.parse
import requests

app = FastAPI()

origins = [
    "https://zabop.github.io",
    # "*" # local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/sum_length_at_date/")
async def sum_length_at_date(relationId: int, date: str):

    # date = "2024-11-20T00:00:00Z"
    # relationId = 1826570

    query = f'[out:json][timeout:50][date:"{date}"];'
    query += f"area({3600000000+relationId})->.searchArea;"  # https://help.openstreetmap.org/questions/77465/how-to-make-area-from-specific-node-or-relation-using-its-element-id-number-in-overpass-ql
    query += """
    (
      way["power"="line"](area.searchArea);
      way["power"="minor_line"](area.searchArea);
    );
    out body;>;out skel qt;
    """

    OVERPASS_URL = "http://overpass-api.de/api/interpreter"
    resp = requests.post(OVERPASS_URL, data={"data": query}).json()

    nodes = {
        e["id"]: (e["lon"], e["lat"]) for e in resp["elements"] if e["type"] == "node"
    }

    ways = []
    for element in resp["elements"]:
        if element["type"] == "way":
            ways.append(
                shapely.geometry.LineString(
                    [nodes[node_id] for node_id in element["nodes"]]
                )
            )

    gdf = gpd.GeoDataFrame(geometry=ways).set_crs("4326")
    gdf = gdf.to_crs(gdf.estimate_utm_crs())
    return {"length": int(gdf.geometry.length.sum()), "overpass_query": "http://overpass-turbo.eu/?Q="+urllib.parse.quote(query)+"&R"}
