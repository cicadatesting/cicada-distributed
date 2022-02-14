package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"

	"github.com/cicadatesting/backend/api"
	"github.com/cicadatesting/backend/cmd"
	"github.com/cicadatesting/backend/pkg/application"
	"github.com/cicadatesting/backend/pkg/badgercommands"
	"github.com/cicadatesting/backend/pkg/datastore"
	"github.com/cicadatesting/backend/pkg/rediscommands"
	"github.com/cicadatesting/backend/pkg/scheduling"
	"github.com/dgraph-io/badger/v3"
	"github.com/docker/docker/client"
	"github.com/go-redis/redis/v8"
	"github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

func teardown(teardownFns [](func() error)) error {
	errors := []string{}

	for _, teardownFn := range teardownFns {
		err := teardownFn()

		if err != nil {
			errors = append(errors, err.Error())
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("Teardown errors: %s", strings.Join(errors, ","))
	}

	return nil
}

func main() {
	teardownFns := [](func() error){}

	datastoreType := os.Getenv("DATASTORE_TYPE")
	logLevel := os.Getenv("LOG_LEVEL")
	var datastoreInstance application.Datastore

	if logLevel == "DEBUG" {
		logrus.SetLevel(logrus.DebugLevel)
	} else {
		logrus.SetLevel(logrus.ErrorLevel)
	}

	if datastoreType == "REDIS" {
		// Initialize redis
		redisAddress := os.Getenv("REDIS_ENDPOINT")

		if redisAddress == "" {
			redisAddress = "cicada-distributed-redis"
		}

		rds := redis.NewClient(&redis.Options{
			Addr:     fmt.Sprintf("%s:6379", redisAddress),
			Password: "", // no password set
			DB:       0,  // use default DB
		})

		datastoreInstance = datastore.NewMemoryDatastore(
			rediscommands.NewRedisCommands(rds),
		)
	} else {
		db, err := badger.Open(
			badger.DefaultOptions("").WithInMemory(true).WithLoggingLevel(badger.WARNING),
		)

		if err != nil {
			log.Fatalf("Failed to create in memory database: %v", err)
		}

		datastoreInstance = datastore.NewMemoryDatastore(
			badgercommands.NewBadgerCommands(db),
		)

		defer db.Close()
	}

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
	} else {
		localScheduler := scheduling.NewLocalScheduler()

		teardownFns = append(teardownFns, localScheduler.Teardown)
		scheduler = localScheduler
	}

	// create server
	s := grpc.NewServer()
	backend := application.NewBackend(datastoreInstance, scheduler)

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	wg := sync.WaitGroup{}
	wg.Add(1)

	go func() {
		<-sigCh

		logrus.Debug("tearing down")

		teardown(teardownFns)
		s.Stop()

		logrus.Debug("finished teardown")
		wg.Done()
	}()

	server := cmd.NewServer(backend)

	lis, err := net.Listen("tcp", "[::]:8283")

	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	api.RegisterBackendServer(s, server)
	logrus.Debug("server listening at", lis.Addr())

	if err := s.Serve(lis); err != nil {
		logrus.Error("failed to serve:", err)
	}

	wg.Wait()
}
