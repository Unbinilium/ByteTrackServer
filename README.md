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
    "timestamp": 1703406577.116568
}
```

### POST

#### Create or attach detection results to a session

Request:

```sh
curl -X POST http://127.0.0.1:8000 \
    -H "Content-Type: application/json" \
    -H "Session-Id: 72d6be50" \
    -d "{\"boxes\": [[20, 23, 12, 24, 89, 0], [12, 34, 45, 56, 78, 1]]}"
```

Response:

```json
{
  "tracked_boxes": [
    [
      20,
      23,
      12,
      24,
      89,
      0,
      1
    ],
    [
      12,
      34,
      45,
      56,
      78,
      1,
      2
    ]
  ],
  "tracker_perf": [
    0.001
  ],
  "timestamp": 1703413614.3132002
}
```

#### Create or attach detection results to a session with image

Request:

```sh
curl -X POST http://127.0.0.1:8000 \
    -H "Content-Type: application/json" \
    -H "Session-Id: 72d6be50" \
    -d "{\"boxes\": [[20, 23, 12, 24, 89, 0], [12, 34, 45, 56, 78, 1]], \"image\": \"{BASE64_IMAGE}\"}"
```

Response:

```json
{
  "tracked_boxes": [
    [
      20,
      23,
      12,
      24,
      89,
      0,
      1
    ],
    [
      12,
      34,
      45,
      56,
      78,
      1,
      2
    ]
  ],
  "annotated_image": "{BASE64_IMAGE}",
  "tracker_perf": [
    0.001,
    0.0
  ],
  "timestamp": 1703414603.4676962
}
```

### DELETE

#### Remove a active session

Request:

```sh
curl -X DELETE http://127.0.0.1:8000 \
    -H "Session-Id: 72d6be50"
```

Response:

```json
{
  "sessions": [],
  "active_threads": 2,
  "timestamp": 1703414872.097493
}
```
