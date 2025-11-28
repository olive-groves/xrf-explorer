from flask import request, jsonify

@app.route("/api/<data_source>/stitch_datacubes/", methods=["POST"])
def stitch_datacubes(data_source: str):
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    if data.get("type") != "elementral" and data.get("type") != "spectral":
        return jsonify({"error": "type must be 'elementral/spectral'"}), 400

    if not isinstance(data.get("preview"), bool):
        return jsonify({"error": "preview must be boolean"}), 400

    if not isinstance(data.get("contextual_image"), str):
        return jsonify({"error": "contextual_image must be string"}), 400

    down_scaling = data.get("down_scaling")
    if not (isinstance(down_scaling, (int, float)) and 0 < down_scaling <= 1):
        return jsonify({"error": "down_scaling must be a number in (0,1]"}), 400

    fragments = data.get("fragments")
    if not isinstance(fragments, list) or not fragments:
        return jsonify({"error": "fragments must be a non-empty list"}), 400

    for i, frag in enumerate(fragments):

        if not isinstance(frag, dict):
            return jsonify({"error": f"fragments[{i}] must be an object"}), 400

        for key in ("datacube_file", "rpl_file"):
            if not isinstance(frag.get(key), str):
                return jsonify({"error": f"fragments[{i}].{key} must be string"}), 400

        if frag.get("rotation") not in {0, 90, 180, 270}:
            return jsonify({"error": f"fragments[{i}].rotation must be 0,90,180,270"}), 400

        for pts_key in ("local_points", "target_points"):
            pts = frag.get(pts_key)
            if not isinstance(pts, dict):
                return jsonify({"error": f"fragments[{i}].{pts_key} must be object"}), 400

            for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
                if not isinstance(pts.get(corner), int):
                    return jsonify({
                        "error": f"fragments[{i}].{pts_key}.{corner} must be int"
                    }), 400

    return jsonify({"status": "ok", "parsed": data}), 200
