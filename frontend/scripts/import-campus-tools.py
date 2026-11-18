"""Import public NCU accessibility records and the OSM walking network."""

import argparse
import json
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

NCU_URL = "https://love.adm.ncu.edu.tw/NCU_counsel/NCU-barrier-free/"
OSM_URL = "https://api.openstreetmap.org/api/0.6/map?bbox=121.1843596,24.9635065,121.1980519,24.9722322"
WAY_KEYS = ("highway", "access", "foot", "wheelchair", "lit", "incline", "smoothness")
NODE_KEYS = ("barrier", "access", "foot", "wheelchair", "kerb")
FACILITIES = ("Elevator", "Ramp", "Toilet", "Parking")


def accessibility(path):
    html = path.read_text(encoding="utf-8")
    points = {
        code: [float(lon), float(lat)]
        for code, lat, lon in re.findall(
            r'\["(\w+)",new google\.maps\.LatLng\(([\d.]+),([\d.]+)\)\]', html
        )
    }
    records = []
    for code, index, quote, title, info in re.findall(
        r"""case"(\w+)":a=neighborhoods\[(\d+)\]\[1\];title=(["'])(.*?)\3;(.*?)break""",
        html,
    ):
        # The source calls the pool marker SwimP and the corresponding menu entry SwimB.
        point_code = "SwimP" if code == "SwimB" else code
        if list(points)[int(index)] != point_code:
            raise ValueError(f"Campus point and record differ for {code}")
        records.append({
            "id": code,
            "name": re.split(r" (?=[A-Z])", title, maxsplit=1)[0],
            "coordinates": points[point_code],
            "facilities": [
                facility.lower() for facility in FACILITIES
                if f'BarrierFree{facility}="1"' in info
            ],
        })
    if not points or len(records) != len(points):
        raise ValueError("The accessibility map format or record count changed")
    return {"source": NCU_URL, "retrieved": date.today().isoformat(), "places": records}


def tagged(element, keys):
    return {
        tag.attrib["k"]: tag.attrib["v"]
        for tag in element.findall("tag") if tag.attrib["k"] in keys
    }


def network(path):
    root = ElementTree.parse(path).getroot()
    ways = []
    used_nodes = set()
    for way in root.findall("way"):
        tags = tagged(way, WAY_KEYS)
        if "highway" not in tags:
            continue
        refs = [int(ref.attrib["ref"]) for ref in way.findall("nd")]
        used_nodes.update(refs)
        ways.append({"id": int(way.attrib["id"]), "nodes": refs, "tags": tags})

    nodes = {}
    for node in root.findall("node"):
        node_id = int(node.attrib["id"])
        if node_id in used_nodes:
            nodes[node_id] = [
                float(node.attrib["lon"]), float(node.attrib["lat"]), tagged(node, NODE_KEYS)
            ]
    if not ways or used_nodes != nodes.keys():
        raise ValueError("The OSM extract is missing network nodes")
    metadata = root.find("meta")
    return {
        "source": OSM_URL,
        "licence": "https://www.openstreetmap.org/copyright",
        "retrieved": date.today().isoformat(),
        "osm_base": metadata.get("osm_base") if metadata is not None else None,
        "ways": ways,
        "nodes": nodes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ncu_html", type=Path)
    parser.add_argument("osm_xml", type=Path)
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "public" / "data"
    for filename, data in (
        ("campus-accessibility.json", accessibility(args.ncu_html)),
        ("campus-walking-network.json", network(args.osm_xml)),
    ):
        (output / filename).write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )
