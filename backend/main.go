package main

import (
	"fmt"
	"log"
	"net"
	"os"

	"github.com/cicadatesting/backend/api"
	"github.com/cicadatesting/backend/cmd"
	"github.com/cicadatesting/backend/pkg/application"
	"github.com/cicadatesting/backend/pkg/datastore"
	"github.com/cicadatesting/backend/pkg/rediscommands"
	"github.com/cicadatesting/backend/pkg/scheduling"
	"github.com/docker/docker/client"
	"github.com/go-redis/redis/v8"
	"google.golang.org/grpc"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

func main() {
	// Initialize redis
	redisAddress := os.Getenv("REDIS_ENDPOINT")

	if redisAddress == "" {
		redisAddress = "cicada-distributed-redis"
	}

	s := grpc.NewServer()
	rds := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:6379", redisAddress),
		Password: "", // no password set
		DB:       0,  // use default DB
	})

	datastore := datastore.NewRedisDatastore(
		rediscommands.NewRedisCommands(rds),
	)

	// initialize scheduling client
	runnerType := os.Getenv("RUNNER_TYPE")
	var scheduler application.Scheduler

	if runnerType == "DOCKER" {
		dockerClient, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())

		if err != nil {
			log.Fatalf("Failed to start docker client: %v", err)
		}

		scheduler = scheduling.NewDockerScheduler(dockerClient)
	} else if runnerType == "KUBE" {
		// NOTE: for local kube client:
		// kubeconfig := os.Getenv("HOME") + "/.kube/config"

		// // Create a Config (k8s.io/client-go/rest)
		// config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
		// if err != nil {
		// 	panic(err.Error())
		// }

		// // Create an API Clientset (k8s.io/client-go/kubernetes)
		// clientset, err := kubernetes.NewForConfig(config)

		// kuberunner := pkg.KubeRunner{
		// 	Clientset: clientset,
		// }

		config, err := rest.InClusterConfig()

		if err != nil {
			log.Fatalf("Failed to create in cluster config: %v", err)
		}

		clientset, err := kubernetes.NewForConfig(config)

		if err != nil {
			log.Fatalf("Failed to create kube clientset: %v", err)
		}

		scheduler = scheduling.NewKubeScheduler(clientset)
	}

	// create server
	backend := application.NewBackend(datastore, scheduler)

	server := cmd.NewServer(backend)

	lis, err := net.Listen("tcp", "[::]:8283")

	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	api.RegisterBackendServer(s, server)
	log.Printf("server listening at %v", lis.Addr())

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
