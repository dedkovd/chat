# chat
Websockets chat

Build docker container:

```
docker build -t chat:0.1 ./
```

Run docker container:

```
docker run -p 8888:8888 -p 6379:6379 chat:0.1
```
