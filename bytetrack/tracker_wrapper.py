import time
import logging
from threading import Lock

from supervision import Detections, ByteTrack, BoundingBoxAnnotator, LabelAnnotator, TraceAnnotator

from bytetrack.sscma_utilitiy import (from_sscma_detection,
                                      detection_to_tracked_bboxs,
                                      image_from_base64,
                                      image_to_base64_jpeg)

Detections.from_sscma_detection = from_sscma_detection


class TrackerWrapper:
    def __init__(self):
        self.lock = Lock()
        self.tracker = ByteTrack()
        self.box_annotator = BoundingBoxAnnotator()
        self.label_annotator = LabelAnnotator()
        self.trace_annotator = TraceAnnotator()

    def track_with_detections(self, requset: dict) -> dict:
        self.lock.acquire()
        result = dict()
        tracker_perf = list()
        try:
            start = time.time()
            detections = Detections.from_sscma_detection(requset)
            detections = self.tracker.update_with_detections(detections)
            tracker_perf.append(round(time.time() - start, 3))
            result['tracked_boxes'] = detection_to_tracked_bboxs(detections)
            if 'image' in requset.keys():
                try:
                    start = time.time()
                    image = image_from_base64(requset['image'])
                    labels = [
                        f"#{tracker_id} {class_id}"
                        for class_id, tracker_id
                        in zip(detections.class_id, detections.tracker_id)
                    ]
                    annotated_image = self.box_annotator.annotate(
                        scene=image.copy(),
                        detections=detections)
                    annotated_labeled_image = self.label_annotator.annotate(
                        scene=annotated_image,
                        detections=detections,
                        labels=labels)
                    traced_annotated_labeled_image = self.trace_annotator.annotate(
                        annotated_labeled_image,
                        detections=detections)
                    tracker_perf.append(round(time.time() - start, 3))
                    result['annotated_image'] = image_to_base64_jpeg(traced_annotated_labeled_image)
                except ValueError:
                    logging.warning('Failed to annotate image')
        except ValueError:
            logging.warning('Failed to track detections')
        result['tracker_perf'] = tracker_perf
        self.lock.release()
        return result
