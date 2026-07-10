#Docker

To run in Docker, use this simple Dockerfile and build the image by running a command like:

```
docker build -t homely-tools .
```

You can then create and run the container by issuing the following:

```
docker run -d -e HOMELY_USER=<mailaddress> -e HOMELY_PASSWORD=<password> -e MQTT_SERVER=<mqtt-servername> --name homely-tools homely-tools:latest
```

