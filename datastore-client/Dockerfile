FROM golang:alpine3.12

WORKDIR /app

COPY go.mod .
COPY go.sum .
RUN go mod download

COPY . .
RUN go build -o main .

EXPOSE 8283

ENTRYPOINT [ "/app/main" ]
