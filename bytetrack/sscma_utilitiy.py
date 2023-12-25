import json
import logging
import base64

import numpy as np
import cv2

from supervision import Detections


def parse_bytes_to_json(request: bytes) -> dict:
    try:
        request_json = json.loads(request)
        if not isinstance(request_json, dict):
            raise ValueError
        return request_json
    except Exception as exc:
        logging.warning('Failed to parse request to json to dict')
        raise ValueError from exc

def xywh_to_xyxy(xywh: np.ndarray) -> np.ndarray:
    xyxy = np.asarray(xywh[:4])
    xyxy[2:4] = xyxy[2:4] + xyxy[0:2]
    return xyxy

def xyxy_to_xywh(xyxy: np.ndarray) -> np.ndarray:
    xywh = np.asarray(xyxy[:4])
    xywh[2:4] = xywh[2:4] - xywh[0:2]
    return xywh

def cxcywh_to_xyxy(cxcywh: np.ndarray) -> np.ndarray:
    xyxy = np.asarray(cxcywh[:4])
    xyxy[0:2] = xyxy[0:2] - (xyxy[2:4] / 2.0)
    xyxy[2:4] = xyxy[0:2] + xyxy[2:4]
    return xyxy

def xyxy_to_cxcywh(xyxy: np.ndarray) -> np.ndarray:
    cxcywh = np.asarray(xyxy[:4])
    cxcywh[2:4] = cxcywh[2:4] - cxcywh[0:2]
    cxcywh[0:2] = cxcywh[0:2] + (cxcywh[2:4] / 2.0)
    return cxcywh

@classmethod
def from_sscma_detection(cls: Detections, detection: dict) -> Detections:
    if not 'boxes' in detection:
        logging.warning('Failed to parse json')
        raise ValueError
    boxes = detection['boxes'] # [x,y,w,h,conf,class_id]

    try:
        boxes = np.asarray(boxes)
        if len(boxes.shape) > 2:
            raise ValueError
        if len(boxes.shape) == 2 and boxes.shape[1] != 6:
                raise ValueError
    except Exception as exc:
        logging.warning('Failed to convert boxes to numpy array')
        raise ValueError from exc

    CONFIDENCE = 4
    CLASS_ID = 5
    LEN = len(boxes)
    xyxys = np.empty((LEN, 4))
    confidences = np.empty((LEN))
    class_ids = np.empty((LEN), dtype=int)
    for i, box in enumerate(boxes):
        xyxys[i] = xywh_to_xyxy(box)
        confidences[i] = box[CONFIDENCE] / 100.0
        class_ids[i] = box[CLASS_ID]

    return cls(
        xyxy=xyxys,
        confidence=confidences,
        class_id=class_ids)

def detection_to_tracked_bboxs(detection: Detections) -> list:
    cxcywhs = np.round([xyxy_to_cxcywh(xyxy) for xyxy in detection.xyxy]).astype(int).tolist()
    confidences = np.round(detection.confidence * 100.0).astype(int).tolist()
    class_ids = detection.class_id.astype(int).tolist()
    tracker_ids = detection.tracker_id.tolist()
    return [[*cxcywh, conf, class_id, tracker_id]
             for cxcywh, conf, class_id, tracker_id in zip(cxcywhs, confidences, class_ids, tracker_ids)]

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
