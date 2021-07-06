package pkg

import (
	"context"
	"fmt"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/api/types/network"
	v1 "github.com/opencontainers/image-spec/specs-go/v1"
)

// type DockerVolume struct {
// 	Source      string
// 	Destination string
// }

type DockerClient interface {
	NetworkInspect(ctx context.Context, networkID string, options types.NetworkInspectOptions) (types.NetworkResource, error)
	NetworkCreate(ctx context.Context, name string, options types.NetworkCreate) (types.NetworkCreateResponse, error)
	ContainerCreate(ctx context.Context, config *container.Config, hostConfig *container.HostConfig, networkingConfig *network.NetworkingConfig, platform *v1.Platform, containerName string) (container.ContainerCreateCreatedBody, error)
	ContainerStart(ctx context.Context, containerID string, options types.ContainerStartOptions) error
	ContainerStop(ctx context.Context, containerID string, timeout *time.Duration) error
	ContainerList(ctx context.Context, options types.ContainerListOptions) ([]types.Container, error)
}

type DockerRunner struct {
	Client DockerClient
}

func NewDockerRunner(client DockerClient) *DockerRunner {
	return &DockerRunner{Client: client}
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

func (r *DockerRunner) StartContainer(
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

	resp, err := r.Client.ContainerCreate(
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
		return err
	}

	if err := r.Client.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return err
	}

	return nil
}

func (r *DockerRunner) StopContainer(name string, labels map[string]string) error {
	ctx := context.Background()
	stopContainerTimeout := time.Second * 3

	if len(labels) != 0 {
		filter := filters.NewArgs()

		for key, value := range labels {
			filter.Add("label", fmt.Sprintf("%s=%s", key, value))
		}

		// NOTE: docker errors if no containers found with filter (but will not throw a known error)
		containers, err := r.Client.ContainerList(context.Background(), types.ContainerListOptions{
			Filters: filter,
		})

		if err != nil {
			return err
		}

		for _, container := range containers {
			err := r.Client.ContainerStop(ctx, container.ID, &stopContainerTimeout)

			if err != nil {
				return err
			}
		}

		return nil
	}

	return r.Client.ContainerStop(ctx, name, &stopContainerTimeout)
}
