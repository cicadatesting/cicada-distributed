package main

import (
	"log"
	"net"

	"github.com/cicadatesting/datastore-client/api"
	"github.com/cicadatesting/datastore-client/cmd"
	"github.com/go-redis/redis/v8"
	"google.golang.org/grpc"
)

func main() {
	lis, err := net.Listen("tcp", "[::]:8283")

	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	rds := redis.NewClient(&redis.Options{
		Addr:     "cicada-distributed-redis:6379",
		Password: "", // no password set
		DB:       0,  // use default DB
	})

	server := cmd.NewServer(rds)

	api.RegisterDatastoreServer(s, server)
	log.Printf("server listening at %v", lis.Addr())

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
