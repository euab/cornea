# Cornea
Cornea is a server that can take multiple video streams and perform facial
recognition on them, returning the face match and the confidence value.

There is no support for training models with this yet, I have trained a model
using OpenCVs `LPBHFaceRecognizer`
for the actual facial recognition process. Adding support for training a model
will be simple to initially implement and is the next thing to do.
Currently Cornea is only capable of receiving data frame by frame by use of a
REST API.

## Example usage
In this example we send a base 64 encoded frame to the API using the Python
Requests module and receive back a confidence rating between 0 and 1.

```py
import requests

res = requests.post(
    'localhost:8000/detect_frame', json={
        "frame": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgI..."
    }
)

print(res)
```
Which could return an output similar to:
```py
>>> {
        'tag': 1,
        'confidence': 0.5711379345492313,
        'position': {
            'x': 555,
            'y': 179,
            'w': 177,
            'h': 177
        }
    }
```

## Installation
To install and use run
```bash
$ git clone https://github.com/euab/cornea.git
```
```bash
$ cd cornea
```
```bash
$ python3 -m cornea
```
As said above, for the moment, you do need a model which has been trained
on faces using OpenCV's `LPBHFaceRecognizer`.
