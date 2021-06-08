FROM golang:alpine3.12

WORKDIR /app

COPY . .

RUN go mod download
RUN go build -o main .
EXPOSE 50052

ENTRYPOINT [ "/app/main" ]
