package scheduling

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/client"
)

type DockerScheduler struct {
	client iDockerClient
}

type DockerSchedulingMetadata struct {
	Image   string  `json:"image"`
	Network *string `json:"network"`
}

func NewDockerScheduler(client *client.Client) *DockerScheduler {
	dc := dockerClient{client: client}

	return &DockerScheduler{client: &dc}
}

func (s *DockerScheduler) CreateTest(
	testID, backendAddress, schedulingMetadata string,
	tags []string,
	env map[string]string,
) error {
	// load scheduling metadata
	dockerSchedulingMetadata := DockerSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &dockerSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	tagArg := GetTagArg(tags)

	// start test container
	err = s.client.startContainer(
		dockerSchedulingMetadata.Image,
		testID,
		append([]string{
			"run-test",
			"--test-id",
			testID,
			"--backend-address",
			backendAddress,
		}, tagArg...),
		map[string]string{"type": "cicada-distributed-test", "test": testID},
		env,
		dockerSchedulingMetadata.Network,
	)

	if err != nil {
		return fmt.Errorf("Error starting test docker container: %v", err)
	}

	return nil
}

func (s *DockerScheduler) CreateScenario(
	testID,
	scenarioID,
	scenarioName,
	backendAddress,
	schedulingMetadata,
	encodedContext string,
	env map[string]string,
) error {
	// load scheduling metadata
	dockerSchedulingMetadata := DockerSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &dockerSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	// start scenario container
	err = s.client.startContainer(
		dockerSchedulingMetadata.Image,
		scenarioID,
		[]string{
			"run-scenario",
			"--name",
			scenarioName,
			"--test-id",
			testID,
			"--scenario-id",
			scenarioID,
			"--encoded-context",
			encodedContext,
			"--backend-address",
			backendAddress,
		},
		map[string]string{
			"type":     "cicada-distributed-scenario",
			"test":     testID,
			"scenario": scenarioName,
		},
		env,
		dockerSchedulingMetadata.Network,
	)

	if err != nil {
		return fmt.Errorf("Error starting scenario docker container: %v", err)
	}

	return nil
}

func (s *DockerScheduler) CreateUserManagers(
	userManagerIDs []string,
	testID, scenarioName, backendAddress, schedulingMetadata, encodedContext string,
	env map[string]string,
) error {
	// load scheduling metadata
	dockerSchedulingMetadata := DockerSchedulingMetadata{}

	err := json.Unmarshal([]byte(schedulingMetadata), &dockerSchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error loading scheduling metadata: %v", err)
	}

	for _, userManagerID := range userManagerIDs {
		err := s.client.startContainer(
			dockerSchedulingMetadata.Image,
			userManagerID,
			[]string{
				"run-user",
				"--name",
				scenarioName,
				"--user-manager-id",
				userManagerID,
				"--backend-address",
				backendAddress,
				"--encoded-context",
				encodedContext,
			},
			map[string]string{
				"type":     "cicada-distributed-user",
				"test":     testID,
				"scenario": scenarioName,
			},
			env,
			dockerSchedulingMetadata.Network,
		)

		if err != nil {
			return fmt.Errorf("Error starting user manager docker container: %v", err)
		}
	}

	return nil
}

func (s *DockerScheduler) StopUserManagers(userManagerIDs []string, schedulingMetadata string) error {
	for _, userManagerID := range userManagerIDs {
		err := s.client.stopContainer(userManagerID)

		if err != nil {
			return fmt.Errorf("Error stopping user manager: %v", err)
		}
	}

	return nil
}

func (s *DockerScheduler) CleanTestInstances(testID, schedulingMetadata string) error {
	err := s.client.stopContainers(map[string]string{"test": testID})

	if err != nil {
		return fmt.Errorf("Error stopping test instances: %v", err)
	}

	return nil
}

func (s *DockerScheduler) CheckTestInstance(instanceID string, schedulingMetadata string) (bool, error) {
	return s.client.containerIsRunning(instanceID), nil
}

// type DockerVolume struct {
// 	Source      string
// 	Destination string
// }

type iDockerClient interface {
	startContainer(image, name string, command []string, labels, env map[string]string, network *string) error
	stopContainer(name string) error
	stopContainers(labels map[string]string) error
	containerIsRunning(name string) bool
}

type dockerClient struct {
	client *client.Client
}

// func (r *DockerRunner) networkExists(network string) (bool, error) {
// 	ctx := context.Background()

// 	_, err := r.Client.NetworkInspect(ctx, network, types.NetworkInspectOptions{})

// 	if client.IsErrNotFound(err) {
// 		return false, nil
// 	} else if err != nil {
// 		return false, err
// 	}

// 	return true, nil
// }

// func (r *DockerRunner) createNetwork(network string) error {
// 	ctx := context.Background()

// 	_, err := r.Client.NetworkCreate(ctx, network, types.NetworkCreate{})

// 	if err != nil {
// 		return err
// 	}

// 	return nil
// }

// func (r *DockerRunner) configureNetwork(network string, createNetwork bool) error {
// 	exists, err := r.networkExists(network)

// 	if !exists && createNetwork {
// 		return r.createNetwork(network)
// 	} else if err != nil {
// 		return err
// 	}

// 	return nil
// }

func (c *dockerClient) startContainer(
	image string,
	name string,
	command []string,
	labels map[string]string,
	env map[string]string,
	// volumes []DockerVolume,
	// hostPort *int,
	// containerPort *int,
	network *string,
	// createNetwork *bool,
) error {
	ctx := context.Background()

	// if network != nil {
	// 	cn := true

	// 	if createNetwork != nil {
	// 		cn = *createNetwork
	// 	}

	// 	err := r.configureNetwork(*network, cn)

	// 	if err != nil {
	// 		return err
	// 	}
	// }

	// portMap := nat.PortMap{}

	// if (network != nil && *network != "host") && containerPort != nil && hostPort != nil {
	// 	portMap[nat.Port(fmt.Sprintf("%v/tcp", *containerPort))] = []nat.PortBinding{
	// 		{HostIP: "::", HostPort: fmt.Sprintf("%v", *hostPort)},
	// 	}
	// }

	// binds := []string{}

	// for _, volume := range volumes {
	// 	binds = append(binds, fmt.Sprintf("%s:%s:rw", volume.Source, volume.Destination))
	// }

	networkMode := "cicada-distributed-network"

	if network != nil {
		networkMode = *network
	}

	resp, err := c.client.ContainerCreate(
		ctx,
		&container.Config{
			Image:  image,
			Cmd:    command,
			Tty:    false,
			Env:    []string{},
			Labels: labels,
		},
		&container.HostConfig{
			// Binds:        binds,
			// PortBindings: portMap,
			NetworkMode: container.NetworkMode(networkMode),
		},
		nil,
		nil,
		name,
	)

	if err != nil {
		return fmt.Errorf("Error creating container: %v", err)
	}

	if err := c.client.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return fmt.Errorf("Error starting container: %v", err)
	}

	return nil
}

func (c *dockerClient) stopContainer(name string) error {
	ctx := context.Background()
	stopContainerTimeout := time.Second * 3

	return c.client.ContainerStop(ctx, name, &stopContainerTimeout)
}

func (c *dockerClient) stopContainers(labels map[string]string) error {
	ctx := context.Background()
	stopContainerTimeout := time.Second * 3
	filter := filters.NewArgs()

	for key, value := range labels {
		filter.Add("label", fmt.Sprintf("%s=%s", key, value))
	}

	// NOTE: docker errors if no containers found with filter (but will not throw a known error)
	containers, err := c.client.ContainerList(context.Background(), types.ContainerListOptions{
		Filters: filter,
	})

	if err != nil {
		return fmt.Errorf("Error listing containers: %v", err)
	}

	for _, container := range containers {
		err := c.client.ContainerStop(ctx, container.ID, &stopContainerTimeout)

		if err != nil {
			return fmt.Errorf("Error stopping container: %v", err)
		}
	}

	return nil
}

func (c *dockerClient) containerIsRunning(name string) bool {
	_, err := c.client.ContainerTop(context.Background(), name, []string{})

	if err != nil {
		return false
	}

	return true
}
