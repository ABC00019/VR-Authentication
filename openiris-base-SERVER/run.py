'''FOR PRE-PROCESSING OF IRIS IMAGES. 


Enhance, masks, normalization'''



import cv2
import iris
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import convolve2d
import random

random.seed(100)
# 1. Create IRISPipeline object
iris_pipeline = iris.IRISPipeline()

# dirs: Where to load imgs
# datasets: Where to store resulting processed imgs
dirs=["examples/dataset1/","examples/dataset2/"]
datasets=["dataset1","dataset2"]

# ------------------ONLY IF YOU WANT TO CROP AND USE CROPPED IMAGES FOR TESTING---------------------
def center_square_crop(img, pupil_x, pupil_y, half_w, half_h, pad_value=0):
    """
    Returns a (2*half_h+1, 2*half_w+1) crop centered on pupil.
    Uses only original pixels where available; pads missing with pad_value (black by default).
    """
    H, W = img.shape[:2]
    px, py = int(pupil_x), int(pupil_y)
    half_w = int(half_w)
    half_h = int(half_h)

    out_h = 2 * half_h + 1
    out_w = 2 * half_w + 1

    # desired bounds in source
    x1, x2 = px - half_w, px + half_w + 1
    y1, y2 = py - half_h, py + half_h + 1

    # intersection with source
    sx1 = max(0, x1)
    sy1 = max(0, y1)
    sx2 = min(W, x2)
    sy2 = min(H, y2)

    # where it lands in destination
    dx1 = sx1 - x1
    dy1 = sy1 - y1
    dx2 = dx1 + (sx2 - sx1)
    dy2 = dy1 + (sy2 - sy1)

    # canvas filled with pad_value
    if img.ndim == 2:
        out = np.full((out_h, out_w), pad_value, dtype=img.dtype)
    else:
        out = np.full((out_h, out_w, img.shape[2]), pad_value, dtype=img.dtype)

    # paste real pixels
    out[dy1:dy2, dx1:dx2] = img[sy1:sy2, sx1:sx2]
    return out



n = 8
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
edge_px = 3
kedge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_px, edge_px))
window = np.ones((n,n))
window /= np.sum(window)
height,width=576,768
variance_list=[15, 80, 30]

for orig_dir,dataset in zip(dirs, datasets):
    os.makedirs(dataset + '/iris_mask/', exist_ok=True)
    os.makedirs(dataset + '/pupil_mask/', exist_ok=True)
    os.makedirs(dataset + '/Enhance/', exist_ok=True)
    os.makedirs(dataset + '/Unenhance/', exist_ok=True)
    os.makedirs(dataset+'/norm/',exist_ok=True)
    os.makedirs(dataset+'/Enhance_Norm/',exist_ok=True)

    for imgs in os.listdir(orig_dir):
        # 2. Load IR image of an eye
        img_pixels = cv2.imread(orig_dir+imgs, cv2.IMREAD_GRAYSCALE)

        print(imgs)
        try:
            # 3. Perform inference
            # Options for the `eye_side` argument are: ["left", "right"]
            output = iris_pipeline(img_data=img_pixels, eye_side="left")
            vectorization=iris_pipeline.call_trace['vectorization']


            #----------------------IRIS/PUPIL POINTS FOR CROPPING IMAGE-------------------------
            pupil_points = vectorization.pupil_array  # Replace with actual key if different
            iris_points = vectorization.iris_array    # Replace with actual key if different
            h, w = img_pixels.shape[:2]
            unenhanced=img_pixels.copy()

            iris_mask = np.zeros((h, w), dtype=np.uint8)

            iris_pts = np.asarray(iris_points, dtype=np.float32)  # handle lists/tuples/objects
            iris_pts = iris_pts.reshape(-1, 2)                    # ensure Nx2
            iris_pts = np.round(iris_pts).astype(np.int32)        # OpenCV wants int32

            l = int(np.clip(iris_pts[:,0].min(), 0, w-1))
            r = int(np.clip(iris_pts[:,0].max()+1, 0, w))
            t = int(np.clip(iris_pts[:,1].min(), 0, h-1))
            b = int(np.clip(iris_pts[:,1].max()+1, 0, h))

            cv2.fillPoly(iris_mask, [iris_pts], 255)

            normalized_iris=iris_pipeline.call_trace['normalization']

            centers=iris_pipeline.call_trace['eye_center_estimation']

            center_x=centers.iris_x
            center_y=centers.iris_y
            center_p_x=centers.pupil_x
            center_p_y=centers.pupil_y


            # ------------------- Pupil mask from pupil_points -------------- -------------------
            pupil_pts = np.asarray(pupil_points, dtype=np.int32)
            pupil_pts = cv2.convexHull(pupil_pts)  # optional but usually helps
            pupil_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(pupil_mask, [pupil_pts], 255)

            # Don't touch pupil boundary band

            inner_pupil = cv2.erode(pupil_mask, kedge, iterations=1)

            # ------------------- Apply pupil attenuation (conditional) ------------------------
            alpha = 0.35
            cond = (inner_pupil == 255) & (img_pixels < 100)
            img_pixels[cond] = (img_pixels[cond].astype(np.float32) * alpha).astype(np.uint8)

            # ------------------- Apply iris mask + crop to bounding box -----------------------


            half_w = max(center_p_x - l, (r - 1) - center_p_x)
            half_h = max(center_p_y - t, (b - 1) - center_p_y)
            unenhanced_crop = center_square_crop(unenhanced, center_p_x, center_p_y, half_w, half_h, pad_value=0)
            cv2.imwrite(dataset + '/Unenhance/' + imgs, unenhanced_crop)
            
            
            square = center_square_crop(img_pixels, center_p_x, center_p_y, half_w, half_h, pad_value=0)
            pupil_crop=center_square_crop(pupil_mask, center_p_x, center_p_y,  half_w, half_h, pad_value=0)
            iris_crop=center_square_crop(iris_mask, center_p_x, center_p_y,  half_w, half_h, pad_value=0)
            iris_crop[pupil_crop==255]=0
            # --------------------------------- Enhancement -------------------------------------
            im = clahe.apply(square).astype(np.uint8)


            cv2.imwrite(dataset + '/iris_mask/'+imgs, iris_crop)

            cv2.imwrite(dataset + '/pupil_mask/'+imgs, pupil_crop)

            cv2.imwrite(dataset + '/Enhance/'+imgs, im)
            
    # ----------------------------Enhancement DONE---------------------------------------------
            

    # ----------------------------------NORM START---------------------------------------------

            norm_img=iris_pipeline.call_trace['normalization'].normalized_image
            noise_mask = iris_pipeline.call_trace["normalization"].normalized_mask
            noise_mask = noise_mask.astype(np.float32)

            # norm_img = norm_img * noise_mask
            norm_img=cv2.resize(norm_img,(512,64))
            noise_mask=cv2.resize(noise_mask,(512,64))

                
            cv2.imwrite(dataset+'/norm/'+imgs,norm_img)
            
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            im = clahe.apply(norm_img).astype(np.uint8)

            cv2.imwrite(dataset+'/Enhance_Norm/'+imgs,im) 

            
# ----------------------------------NORM DONE----------------------------------------------
        except Exception as e:
            print(f"An error occurred: {e}")

