from xrf_explorer import app


@app.route("/api")
def api():
    """
    Returns a list of all API endpoints.

    :return: list of API endpoints
    """

    routes: list[str] = []

    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api"):
            routes.append(rule.rule)

    routes.sort()

    return routes
