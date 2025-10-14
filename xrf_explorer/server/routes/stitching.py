from xrf_explorer import app
from flask import Flask, request, jsonify

@app.route("/api/<data_source>/stitch/", methods=["POST"])
def stitch_datacubes(data_source: str):
    data = request.get_json(force=True, silent=False)
    errors = []
    frame_width     = data.get("frame_width")
    frame_height    = data.get("frame_height")
    datacube_type   = data.get("datacube_type")
    blendmode       = data.get("blendmode")
    overlap         = data.get("overlap_policy")
    fragments       = data.get("fragments")

    if not isinstance(frame_width, int) or frame_width <= 0:
        errors.append("frame_width must be a non-negative integer.")
    if not isinstance(frame_height, int) or frame_height <= 0:
        errors.append("frame_height must be a non-negative integer.")

    allowed_blend = {"max", "average", "min"}
    if blendmode not in allowed_blend:
        errors.append(f"blendmode must be one of {allowed_blend}.")

    allowed_overlap = {"strict", "lax"}
    if overlap not in allowed_overlap:
        errors.append(f"overlap_policy must be one of {allowed_overlap}.")

    allowed_datacube_types = {"elemental", "spectral"}
    if datacube_type not in allowed_datacube_types:
        errors.append(f"datacube_type must be one of {allowed_datacube_types}.")

    if not isinstance(fragments, list) or len(fragments) == 0:
        errors.append("fragments must be a non-empty list.")
    else:
        for i, frag in enumerate(fragments):
            if not isinstance(frag, dict):
                errors.append(f"fragment[{i}] must be an object.")
                continue
            datacube_index = frag.get("datacube_index")
            fx = frag.get("x")
            fy = frag.get("y")

            if not isinstance(fx, int) or not isinstance(fy, int):
                errors.append(f"fragment[{i}].x and .y must be integers.")

    if errors:
        return jsonify({"status": "error", "errors": errors}), 400

