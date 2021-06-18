package main

import (
	"log"
	"net"

	"github.com/cicadatesting/container-service/api"
	"github.com/cicadatesting/container-service/cmd"
	"github.com/docker/docker/client"
	"google.golang.org/grpc"
)

func main() {
	dockerClient, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())

	if err != nil {
		panic(err)
	}

	lis, err := net.Listen("tcp", "[::]:8284")

	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()

	server := cmd.NewServer(dockerClient)

	api.RegisterContainerServiceServer(s, server)
	log.Printf("server listening at %v", lis.Addr())

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
