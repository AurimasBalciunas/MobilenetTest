import os
import json
import cv2
import numpy as np
import pandas as pd
import time
from backend.utils import timeit, draw_boxed_text

DETECTION_MODEL = 'ssd_mobilenet/'
SWAPRB = False
IMG_W = 300
IMG_H = 300

#https://cristianpb.github.io/blog/ssd-yolo
with open(os.path.join('models', DETECTION_MODEL, 'labels.json')) as json_data:
    CLASS_NAMES = json.load(json_data)


class Detector():
    """Class ssd"""

    @timeit
    def __init__(self):
        self.model = cv2.dnn.readNetFromTensorflow(
                'models/ssd_mobilenet/frozen_inference_graph.pb',
                'models/ssd_mobilenet/ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
        self.colors = np.random.uniform(0, 255, size=(100, 3))

    @timeit
    def prediction(self, image):
        self.model.setInput(
                cv2.dnn.blobFromImage(image, size=(IMG_W, IMG_H), swapRB=SWAPRB))
        output = self.model.forward()
        result = output[0, 0, :, :]
        return result

    @timeit
    def filter_prediction(self, output, image, conf_th=0.5, conf_class=[]):
        height, width = image.shape[:-1]
        df = pd.DataFrame(
                output,
                columns=[
                    '_', 'class_id', 'confidence', 'x1', 'y1', 'x2', 'y2'])
        df = df.assign(
                x1=lambda x: (x['x1'] * width).astype(int).clip(0),
                y1=lambda x: (x['y1'] * height).astype(int).clip(0),
                x2=lambda x: (x['x2'] * width).astype(int),
                y2=lambda x: (x['y2'] * height).astype(int),
                class_name=lambda x: (
                    x['class_id'].astype(int).astype(str).replace(CLASS_NAMES)
                    ),
                # TODO: don't work in python 3.5
                # label=lambda x: (
                #     x.class_name + ': ' + (
                #         x['confidence'].astype(str).str.slice(stop=4)
                #         )
                #     )
                )
        df['label'] = (df['class_name'] + ': ' +
                       df['confidence'].astype(str).str.slice(stop=4))
        df = df[df['confidence'] > conf_th]
        if len(conf_class) > 0:
            df = df[df['class_id'].isin(conf_class)]
        return df

    def draw_boxes(self, image, df):
        for idx, box in df.iterrows():
            x_min, y_min, x_max, y_max = box['x1'], box['y1'], box['x2'], box['y2']
            color = self.colors[int(box['class_id'])]
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)
            txt_loc = (max(x_min+2, 0), max(y_min+2, 0))
            txt = box['label']
            image = draw_boxed_text(image, txt, txt_loc, color)
        return image

#https://stackoverflow.com/questions/28566972/why-are-webcam-images-taken-with-python-so-dark
def get_image_with_ramp_up(imcap,ramp_frames):
    for i in range(ramp_frames):
        temp = imcap.read()
    success, imcap = imcap.read()
    return imcap


if __name__ == "__main__":

    #setting up video capture
    imcap = cv2.VideoCapture(0)
    imcap.set(3,IMG_W)
    imcap.set(4,IMG_H)
    #success, image = imcap.read()



    
    print(CLASS_NAMES)

    detector = Detector()

    while True:
        print("ramped")
        ramp_frames=5
        image = get_image_with_ramp_up(imcap, ramp_frames)
        output = detector.prediction(image)
        df = detector.filter_prediction(output, image)
        print(df)
        cv2.startWindowThread()
        cv2.namedWindow("mobilenet_result")
        image = detector.draw_boxes(image, df)
        cv2.imshow("mobilenet_result", image)
        cv2.waitKey(100)
        #time.sleep(5)
cv2.destroyWindow('face_detect')
cv2.imwrite("./imgs/outputcv.jpg", image)