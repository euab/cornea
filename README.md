# Cornea
Cornea is a server that can take multiple video streams and perform facial
recognition on them, returning the face match and the confidence value.

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
To install and use you will need a working installation of PostgreSQL on your
system.

Once setup run the following commands
```sql
CREATE ROLE cornea WITH LOGIN PASSWORD '<your_password>';
CREATE DATABASE cornea OWNER cornea;
```
Then, go ahead and install and run Cornea:
```bash
$ git clone https://github.com/euab/cornea.git
```
```bash
$ cd cornea
```
```bash
$ python3 -m cornea --run
```
On running the program for the first time, you will be prompted to configure
the database connection according to how the database was created above. Edit
the configuration stored in `config.yml` accordingly. An example is provided:
```yaml
database:
    postgres:
        database: "cornea"
        user: "cornea"
        password: "youshallnotpass"
        host: "127.0.0.1"
        port: 5432
```
## Ingesting training data
Currently, as we haven't implemented few-shot learning, a decent supply of
training data is required to ensure accuracy. The implementation of few-shot
or even one-shot learning methods is planned in the future.
There is a schema for ingesting training data which is that a folder of
training data will contain the training data for one person. You also need to
supply their tag for the moment. So, a command
to ingest training data for one person is:
```bash
# python3 -m cornea --ingest ./my_training_data/person1/ --tag 1
```

## Training
To train a model, ensure that you have a populated database of valid training
data and run:
```bash
$ python3 -m cornea --train
```
Models are outputted in YAML format.
