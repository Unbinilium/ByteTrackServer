import logging
from threading import Lock

import numpy as np

from supervision import (
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
    detection_to_tracked_bboxs,
    image_to_base64,
)


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
        annotation_config = config.annotation_config
        self.box_annotator = BoundingBoxAnnotator(
            thickness=annotation_config.bbox_thickness
        )
        self.label_annotator = LabelAnnotator(
            text_scale=annotation_config.bbox_text_scale,
            text_padding=annotation_config.bbox_text_padding,
        )
        self.labels = config.annotation_config.labels
        self.trace_annotator = TraceAnnotator(
            position=config.trace_config.trace_position,
            trace_length=config.trace_config.trace_length,
            thickness=annotation_config.trace_line_thickness,
        )
        zone_overlay = np.zeros((*self.canva_shape, 4), dtype=np.uint8)
        color_platte = ColorPalette.default()
        self.filter_regions = {}
        for i, (region_name, region_config) in enumerate(config.filter_regions.items()):
            zone = PolygonZone(
                polygon=region_config.polygon,
                frame_resolution_wh=self.canva_shape,
                triggering_position=region_config.triggering_position,
            )
            zone_overlay = PolygonZoneAnnotator(
                zone,
                color_platte.by_idx(i + 10),
                thickness=annotation_config.polygon_thickness,
                text_scale=annotation_config.polygon_text_scale,
                text_padding=annotation_config.polygon_text_padding,
            ).annotate(scene=zone_overlay, label=region_name)
            self.filter_regions[region_name] = zone
        self.backgorund = zone_overlay

    def track_with_detections(self, detections: dict) -> dict:
        with self.lock:
            result = {}
            result["filtered_regions"] = {}
            try:
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
                        f"#{tracker_id} {self.labels[class_id] if class_id in self.labels else class_id}"
                        for class_id, tracker_id in zip(
                            detections.class_id, detections.tracker_id
                        )
                    ],
                )
                traced_annotated_labeled_image = self.trace_annotator.annotate(
                    annotated_labeled_image, detections=detections
                )
                traced_annotated_labeled_image[
                    np.any(traced_annotated_labeled_image[:, :, :3] != 0, axis=-1), 3
                ] = 255
                result["annotated_image_mask"] = image_to_base64(
                    traced_annotated_labeled_image
                )
            except Exception as exc:  # pylint: disable=broad-except
                logging.warning("Failed to track detections", exc_info=exc)
        return result
