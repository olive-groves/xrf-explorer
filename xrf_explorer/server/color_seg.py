import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import cv2
from sklearn.cluster import KMeans


image=cv2.imread("VGM_Package2024007_TUE_XrfExplorer2_Roulin_V20240424/196_1989_RGB.tif")
image2=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

img_1 = cv2.resize(image2, None, fx = 0.1, fy = 0.1)

vectorized = np.float32(img_1.reshape((-1,3)))

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)

K = 10
attempts=10
ret,label,center=cv2.kmeans(vectorized,K,None,criteria,attempts,cv2.KMEANS_PP_CENTERS)

center = np.uint8(center)
res = center[label.flatten()]
result_image = res.reshape((img_1.shape))

plt.figure()
plt.imshow(img_1)
plt.show()
reshaped_im = img_1.reshape((-1, 3))
print(reshaped_im.shape)

k = 20
kmeans = KMeans(k)

kmeans.fit(reshaped_im)

dominant_colors = kmeans.cluster_centers_.astype('uint8')
dominant_colors

plt.figure()
for i,color in enumerate(dominant_colors):
    palette = np.zeros_like(img_1, dtype='uint8')
    palette[:,:,:] = color
    plt.subplot(1,k,i+1)
    plt.axis("off")
    plt.imshow(palette)
print(img_1.shape) 

Sum_of_squared_distances = []
K = range(1,20)
for k in K:
    km = KMeans(n_clusters=k)
    km = km.fit(reshaped_im)
    Sum_of_squared_distances.append(km.inertia_)


plt.plot(K, Sum_of_squared_distances, 'bx-')
plt.xlabel('k')
plt.ylabel('Sum_of_squared_distances')
plt.title('Elbow Method For Optimal k')
plt.show()    