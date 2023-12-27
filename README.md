# ByteTrack HTTP Server

A simple HTTP server for tracking detected bounding boxes using [ByteTrack](https://github.com/ifzhang/ByteTrack).

## Run REST API Server

```sh
python3 server.py
```

Arguments:

- `--host`: host address of the server, default: `127.0.0.1`
- `--port`: port number of the server, default: `8000`
- `--ssl`: enable SSL, default: `False`
- `--ssl_certfile`: SSL certificate file, default: `None`
- `--ssl_keyfile`: SSL key file, default: `None`
- `--max_workers`: maximum number of workers, default: `4`

Virtual environment is recommended.

```sh
conda create -n bytetrack_server python=3.10
conda activate bytetrack_server
```

## API Reference

The server supports the following HTTP methods, using a HTTP debug tool like [HTTPie](https://httpie.io/app) or `curl` to test the API.

### GET

#### Get all active sessions

Requset:

```sh
curl -X GET http://127.0.0.1:8000
```

Response:

```json
{
    "sessions": [],
    "active_threads": 2,
    "status": "OK",
    "message": "Success",
    "timestamp": 1703406577.116568
}
```

#### Create a new session

Request:

```sh
curl -X POST http://127.0.0.1:8000 \
    -H "Content-Type: application/json"
    --data-binary @body.json
```

Request body:

```json
{
    "resolution": [240, 240],
    "tracker_config": {
        "track_thresh": 0.25,
        "track_buffer": 30,
        "match_thresh": 0.8,
        "frame_rate": 30
    },
    "trace_config": {
        "trace_length": 30
    },
    "annotation_config": {
        "label_names": {
            "0": "Person",
            "1": "Car",
            "2": "Bicycle",
            "3": "Motorcycle",
            "4": "Bus",
            "5": "Truck"
        }
    },
    "filter_regions": {
        "Region A": {
            "polygon": [[12, 34], [56, 78], [90, 12], [34, 56]],
            "triggering_position": "CENTER_OF_MASS"
        },
        "Region B": {
            "polygon": [[10, 10], [200, 10], [200,200], [10, 200], [30, 30]],
            "triggering_position": "CENTER"
        }
    }
}
```

Response:

```json
{
    "session_id": "72d6be50",
    "status": "OK",
    "message": "Success",
    "timestamp": 1703406577.116568
}
```

### POST

#### Create or attach detection results to a session

Request:

```sh
curl -X POST http://127.0.0.1:8000/session \
    -H "Content-Type: application/json" \
    --data-binary @body.json
```

Request body:

```json
{
    "session_id": "72d6be50",
    "boxes": [
        [20, 23, 12, 24, 89, 0], [12, 34, 45, 56, 78, 1]
    ]
}
```

Response:

```json
{
    "tracked_boxes": [
        [20, 23, 12, 24, 89, 0, 1],
        [12, 34, 45, 56, 78, 1, 2]
    ],
    "filtered_regions": {
        "Region A": [1],
        "Region B": [1, 2]
    },
    "annotated_image_mask": "data:image/png;base64,...",
    "status": "OK",
    "message": "Success",
    "timestamp": 1703413614.3132002
}
```

### DELETE

#### Remove a active session

Request:

```sh
curl -X DELETE http://127.0.0.1:8000/session \
    -H "Content-Type: application/json" \
    --d "{ \"session_id\": \"72d6be50\" }"
```

Response:

```json
{
    "status": "OK",
    "message": "Success",
    "timestamp": 1703414872.097493
}
```

#### Remove all active sessions

Request:

```sh
curl -X DELETE http://127.0.0.1:8000
```

Response:

```json
{
    "status": "OK",
    "message": "Success",
    "timestamp": 1703414872.097493
}
```
