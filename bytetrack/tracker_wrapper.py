import logging
from threading import Lock

import numpy as np

from supervision import (
    Position,
    Detections,
    ByteTrack,
    BoundingBoxAnnotator,
    LabelAnnotator,
    TraceAnnotator,
    PolygonZone,
    PolygonZoneAnnotator,
    ColorPalette,
)

from bytetrack.utilitiy import (
    SessionConfig,
    from_post_detection,
    detection_to_tracked_bboxs,
    image_to_base64,
)

Detections.from_post_detection = from_post_detection


class TrackerWrapper:
    def __init__(self, config: SessionConfig):
        self.lock = Lock()
        self.canva_shape = config.resolution[:2]
        tracker_config = config.tracker_config
        self.tracker = ByteTrack(
            track_thresh=tracker_config.track_thresh,
            track_buffer=tracker_config.track_buffer,
            match_thresh=tracker_config.match_thresh,
            frame_rate=tracker_config.frame_rate,
        )
        self.box_annotator = BoundingBoxAnnotator()
        self.label_annotator = LabelAnnotator()
        self.label_names = config.annotation_config.label_names
        self.trace_annotator = TraceAnnotator(
            trace_length=config.trace_config.trace_length
        )
        zone_overlay = np.zeros((*self.canva_shape, 4), dtype=np.uint8)
        self.filter_regions = {}
        for i, (region_name, region_config) in enumerate(config.filter_regions.items()):
            zone = PolygonZone(
                polygon=np.asarray(region_config.polygon),
                frame_resolution_wh=self.canva_shape,
                triggering_position=Position(region_config.triggering_position),
            )
            zone_overlay = PolygonZoneAnnotator(
                zone, ColorPalette.default().by_idx(i)
            ).annotate(scene=zone_overlay, label=region_name)
            self.filter_regions[region_name] = zone
        self.backgorund = zone_overlay

    def track_with_detections(self, requset: dict) -> dict:
        with self.lock:
            result = {}
            result["filtered_regions"] = {}
            try:
                detections = Detections.from_post_detection(requset)
                detections = self.tracker.update_with_detections(detections)
                result["tracked_boxes"] = detection_to_tracked_bboxs(detections)

                for region_name, zone in self.filter_regions.items():
                    result["filtered_regions"][region_name] = detections.tracker_id[
                        zone.trigger(detections)
                    ].tolist()

                image = self.backgorund.copy()
                annotated_image = self.box_annotator.annotate(
                    scene=image, detections=detections
                )
                annotated_labeled_image = self.label_annotator.annotate(
                    scene=annotated_image,
                    detections=detections,
                    labels=[
                        f"#{tracker_id} {self.label_names[class_id] if str(class_id) in self.label_names else str(class_id)}"
                        for class_id, tracker_id in zip(
                            detections.class_id, detections.tracker_id
                        )
                    ],
                )
                traced_annotated_labeled_image = self.trace_annotator.annotate(
                    annotated_labeled_image, detections=detections
                )
                result["annotated_image_mask"] = image_to_base64(
                    traced_annotated_labeled_image
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.warning("Failed to track detections", exc_info=exc)
        return result
