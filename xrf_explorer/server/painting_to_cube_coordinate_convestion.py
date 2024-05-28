def get_cube_coordinates(
    rectangle_points_on_base_image: tuple[tuple[int, int], tuple[int, int]],
    base_img_width: int,
    base_img_height: int,
    cube_width: int,
    cube_height: int,
):
    point_1, point_2 = rectangle_points_on_base_image

    x_1, y_1 = point_1
    x_2, y_2 = point_2

    ratio_img_cube_width = base_img_width / cube_width
    ratio_img_cube_height = base_img_height / cube_height

    x_1_new = x_1 * ratio_img_cube_width
    x_2_new = x_2 * ratio_img_cube_width
    y_1_new = y_1 * ratio_img_cube_height
    y_2_new = y_2 * ratio_img_cube_height

    return ((x_1_new, y_1_new), (x_2_new, y_2_new))
