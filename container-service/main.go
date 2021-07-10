package main

import (
	"fmt"
	"log"
	"net"
	"os"

	"github.com/cicadatesting/container-service/api"
	"github.com/cicadatesting/container-service/cmd"
	"github.com/cicadatesting/container-service/pkg"
	"github.com/docker/docker/client"
	"google.golang.org/grpc"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

func getHandler() cmd.Handler {
	runnerType := os.Getenv("RUNNER_TYPE")

	if runnerType == "DOCKER" {
		dockerClient, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())

		if err != nil {
			panic(err)
		}

		runner := pkg.NewDockerRunner(dockerClient)

		return cmd.NewDockerHandler(runner)
	} else if runnerType == "KUBE" {
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
			panic(err)
		}

		clientset, err := kubernetes.NewForConfig(config)

		if err != nil {
			panic(err)
		}

		runner := pkg.NewKubeRunner(clientset)

		return cmd.NewKubeHandler(runner)
	}

	panic(fmt.Errorf("Invalid Runner Type: %s", runnerType))
}

func main() {
	handler := getHandler()

	lis, err := net.Listen("tcp", "[::]:8284")

	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()

	server := cmd.NewServer(handler)

	api.RegisterContainerServiceServer(s, server)
	log.Printf("server listening at %v", lis.Addr())

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
