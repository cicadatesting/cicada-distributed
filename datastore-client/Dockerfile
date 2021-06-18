FROM golang:alpine3.12

WORKDIR /app

COPY . .

RUN go mod download
RUN go build -o main .
EXPOSE 8283

ENTRYPOINT [ "/app/main" ]
