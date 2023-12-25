import json
import logging
import base64

import numpy as np
import cv2

from supervision import Detections


def parse_bytes_to_json(request: bytes) -> dict:
    try:
        request_json = json.loads(request)
        return request_json
    except Exception as exc:
        logging.warning('Failed to parse request to json')
        raise ValueError from exc

def xywh_to_xyxy(xywh: list) -> list:
    xyxy = xywh[:4]
    xyxy[2] = xyxy[0] + xyxy[2]
    xyxy[3] = xyxy[1] + xyxy[3]
    return xyxy

def xyxy_to_xywh(xyxy: list) -> list:
    xywh = xyxy[:4]
    xywh[2] = xywh[2] - xywh[0]
    xywh[3] = xywh[3] - xywh[1]
    return xywh

@classmethod
def from_sscma_detection(cls: Detections, detection: dict) -> Detections:
    if not 'boxes' in detection:
        logging.warning('Failed to parse json')
        raise ValueError
    boxes = detection['boxes'] # [x,y,w,h,conf,class_id]

    try:
        boxes = np.array(boxes)
    except Exception as exc:
        logging.warning('Failed to convert boxes to numpy array')
        raise ValueError from exc

    CONFIDENCE = 4
    CLASS_ID = 5
    xyxys = []
    confidences = []
    class_ids = []
    for box in boxes:
        xyxys.append(xywh_to_xyxy(box))
        confidences.append(box[CONFIDENCE] / 100.0)
        class_ids.append(box[CLASS_ID])

    return cls(
        xyxy=np.asarray(xyxys),
        confidence=np.asarray(confidences),
        class_id=np.asarray(class_ids).astype(int)
    )

def detection_to_tracked_bboxs(detection: Detections) -> list:
    xyxys = np.round(detection.xyxy).astype(int).tolist()
    confidences = np.round(detection.confidence * 100.0).astype(int).tolist()
    class_ids = detection.class_id.astype(int).tolist()
    tracker_ids = detection.tracker_id.tolist()
    return [[*xyxy_to_xywh(xyxy), conf, class_id, tracker_id]
             for xyxy, conf, class_id, tracker_id in zip(xyxys, confidences, class_ids, tracker_ids)]

def image_from_base64(base64_image: str) -> np.ndarray:
    try:
        decoded = base64.b64decode(base64_image)
        image = np.frombuffer(decoded, dtype=np.uint8)
        if len(image) < 1:
            raise ValueError
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    except Exception as exc:
        logging.warning('Failed to convert base64 to jpeg')
        raise ValueError from exc
    return image

def image_to_base64_jpeg(image: np.ndarray) -> str:
    ret, jpeg = cv2.imencode('.jpg', image)
    if not ret:
        logging.warning('Failed to encode image to jpeg')
        raise ValueError
    base64_image = base64.b64encode(jpeg).decode('utf-8')
    return base64_image
