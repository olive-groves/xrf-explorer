import numpy as np

from matplotlib.path import Path


def convert_to_middle_image(point: np.array) -> np.array:
    pass


def polygon_selection(edges: np.array[np.ndarray[int], np.ndarray[int]]) -> np.ndarray:
    """
    https://stackoverflow.com/questions/21339448/how-to-get-list-of-points-inside-a-polygon-in-python

    :param edges:
    :return:
    """

    polygon_outline: Path = Path(edges)

    min_x: int
    max_x: int
    min_y: int
    max_y: int
    min_x, max_x, min_y, max_y = edges[0][0], edges[0][0], edges[0][1], edges[0][1]

    for edge in edges:
        min_x = min(min_x, edge[0])
        max_x = max(max_x, edge[0])

        min_y = min(min_y, edge[1])
        max_y = max(max_y, edge[1])

    # rectangular canvas covering the polygon
    canvas_x: np.ndarray;
    canvas_y: np.ndarray
    canvas_x, canvas_y = np.meshgrid(range(min_x, max_x), range(min_y, max_y))
    canvas_x, canvas_y = canvas_x.flatten(), canvas_y.flatten()
    canvas_points: np.ndarray = np.vstack((canvas_x, canvas_y)).T

    # contained_points[i] = True <=> canvas_points[i] is inside the polygon
    contained_points: np.ndarray[bool] = polygon_outline.contains_points(canvas_points)
    points_selected: np.ndarray = contained_points.reshape(max_x - min_x, max_y - min_y)

    # do we need to scale them?
    # for i in range(len(points_selected)):
    #     points_selected[i][0] += min_x
    #     points_selected[i][1] += min_y

    return points_selected


def box_selection(points: np.ndarray[np.ndarray[int], np.ndarray[int]]) -> np.array:

    top_left: np.array = np.array([min(point[0] for point in points),
                                   min(point[1] for point in points)])
    bottom_right: np.array = np.array([max(point[0] for point in points),
                                       max(point[1] for point in points)])

    edges: np.array = np.array([[top_left[0], top_left[1]],
                               [top_left[0], bottom_right[1]],
                               [bottom_right[0], bottom_right[1]],
                               [bottom_right[0], top_left[1]]])

    return polygon_selection(edges)
