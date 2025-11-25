from transformer import *
import matplotlib.pyplot as plt

rgb = cv.imread("RGB.jpg", cv.IMREAD_GRAYSCALE)
if(rgb is None):
    raise FileNotFoundError("RGB image not found.")
rgb_height, rgb_width = rgb.shape

img_1 = cv.imread("projection1.jpg", cv.IMREAD_GRAYSCALE)
points_img_1 = WarpSelection((40, 88), (566, 25), (92, 534), (669, 544))
points_rgb_1 = WarpSelection((31, 127), (988, 5), (124, 935), (1167, 955))

img_2 = cv.imread("projection2.jpg", cv.IMREAD_GRAYSCALE)
points_img_2 = WarpSelection((19,238), (741,270), (63, 570), (695,560))
points_rgb_2 = WarpSelection((15,1485), (1331,1535), (104, 2100), (1251, 2071))

img_3 = cv.imread("projection3.jpg", cv.IMREAD_GRAYSCALE)
points_img_3 = WarpSelection((207, 48), (666, 29), (117, 499), (762, 519))
points_rgb_3 = WarpSelection((1841, 61), (2678, 20), (1667, 891), (2864, 911))

img_4 = cv.imread("projection4.jpg", cv.IMREAD_GRAYSCALE)
points_img_4 = WarpSelection((94,232), (661,155), (90, 639), (793,761))
points_rgb_4 = WarpSelection((1661,1428), (2702, 1262), (1679, 2161), (2946, 2370))

points = [
    (points_img_1, points_rgb_1),
    (points_img_2, points_rgb_2),
    (points_img_3, points_rgb_3),
    (points_img_4, points_rgb_4),
]

spectral_fragments = [
    SpectralDatacubeFragment.from_file(rf"spectral1.raw", rf"spectral1.rpl", 3 * 90),
    SpectralDatacubeFragment.from_file(rf"spectral2.raw", rf"spectral2.rpl", 3 * 90),
    SpectralDatacubeFragment.from_file(rf"spectral3.raw", rf"spectral3.rpl", 1 * 90),
    SpectralDatacubeFragment.from_file(rf"spectral4.raw", rf"spectral4.rpl", 1 * 90),
]

elemental_fragments = [
    ElementalDatacubeFragment.from_file(rf"element1.dms", 3 * 90),
    ElementalDatacubeFragment.from_file(rf"element2.dms", 3 * 90),
    ElementalDatacubeFragment.from_file(rf"element3.dms", 1 * 90),
    ElementalDatacubeFragment.from_file(rf"element4.dms", 1 * 90),
]

intensity_scales = [0.96, 0.85, 1.0, 0.9]

stitcher = DatacubeStitcher(spectral_fragments, intensity_scales, points, Dimensions(0,0, rgb_width, rgb_height))
#stitcher.stitch_datacubes()
#SpectralDatacubeFragment.from_file(rf"stitched_spectral.raw", rf"stitched_spectral.rpl").unshape_cube("stitched_spectral.raw", "normal_stitched_spectral.raw")

el = SpectralDatacubeFragment.from_file(rf"normal_stitched_spectral.raw", rf"stitched_spectral.rpl")

# #el = ElementalDatacubeFragment.from_file(rf"stitched_elemental.dms")

projection = el.create_greyscale_projection()

plt.figure(figsize=(10, 10))
plt.imshow(projection, cmap='gray', vmin=np.min(projection), vmax=np.max(projection))
plt.axis('off')
plt.title("Warped images placed inside RGB-sized frame")
plt.show()

# display_img = stitcher.stitch_greyscales([img_1,img_2, img_3, img_4])
# plt.figure(figsize=(10, 10))
# plt.imshow(display_img, cmap='gray', vmin=np.min(display_img), vmax=np.max(display_img))
# plt.axis('off')
# plt.title("Warped images placed inside RGB-sized frame")
# plt.show()