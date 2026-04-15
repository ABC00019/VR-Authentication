import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        print(f"Index {i}: OPEN — frame={ret}, size={frame.shape if ret else 'N/A'}")
        cap.release()
    else:
        print(f"Index {i}: not found")