package pkg

import (
	"context"
	"fmt"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	v1 "github.com/opencontainers/image-spec/specs-go/v1"
)

type DockerVolume struct {
	Source      string
	Destination string
}

type DockerClient interface {
	NetworkInspect(ctx context.Context, networkID string, options types.NetworkInspectOptions) (types.NetworkResource, error)
	NetworkCreate(ctx context.Context, name string, options types.NetworkCreate) (types.NetworkCreateResponse, error)
	ContainerCreate(ctx context.Context, config *container.Config, hostConfig *container.HostConfig, networkingConfig *network.NetworkingConfig, platform *v1.Platform, containerName string) (container.ContainerCreateCreatedBody, error)
	ContainerStart(ctx context.Context, containerID string, options types.ContainerStartOptions) error
	ContainerStop(ctx context.Context, containerID string, timeout *time.Duration) error
}

type DockerRunner struct {
	Client DockerClient
}

func (r *DockerRunner) NetworkExists(network string) (bool, error) {
	ctx := context.Background()

	_, err := r.Client.NetworkInspect(ctx, network, types.NetworkInspectOptions{})

	if client.IsErrNotFound(err) {
		return false, nil
	} else if err != nil {
		return false, err
	}

	return true, nil
}

func (r *DockerRunner) CreateNetwork(network string) error {
	ctx := context.Background()

	_, err := r.Client.NetworkCreate(ctx, network, types.NetworkCreate{})

	if err != nil {
		return err
	}

	return nil
}

func (r *DockerRunner) ConfigureNetwork(network string, createNetwork bool) error {
	exists, err := r.NetworkExists(network)

	if !exists && createNetwork {
		return r.CreateNetwork(network)
	} else if err != nil {
		return err
	}

	return nil
}

func (r *DockerRunner) StartContainer(
	image string,
	name string,
	command []string,
	labels []string,
	env map[string]string,
	volumes []DockerVolume,
	hostPort *int,
	containerPort *int,
	network *string,
	createNetwork *bool,
) error {
	ctx := context.Background()

	if network != nil {
		cn := true

		if createNetwork != nil {
			cn = *createNetwork
		}

		err := r.ConfigureNetwork(*network, cn)

		if err != nil {
			return err
		}
	}

	portMap := nat.PortMap{}

	if (network != nil && *network != "host") && containerPort != nil && hostPort != nil {
		portMap[nat.Port(fmt.Sprintf("%v/tcp", *containerPort))] = []nat.PortBinding{
			{HostIP: "::", HostPort: fmt.Sprintf("%v", *hostPort)},
		}
	}

	binds := []string{}

	for _, volume := range volumes {
		binds = append(binds, fmt.Sprintf("%s:%s:rw", volume.Source, volume.Destination))
	}

	networkMode := "cicada-distributed-network"

	if network != nil {
		networkMode = *network
	}

	labelMap := map[string]string{"cicada-distributed": ""}

	for _, label := range labels {
		labelMap[label] = ""
	}

	resp, err := r.Client.ContainerCreate(
		ctx,
		&container.Config{
			Image:  image,
			Cmd:    command,
			Tty:    false,
			Env:    []string{},
			Labels: labelMap,
		},
		&container.HostConfig{
			Binds:        binds,
			PortBindings: portMap,
			NetworkMode:  container.NetworkMode(networkMode),
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

func (r *DockerRunner) StopContainer(containerID string) error {
	ctx := context.Background()
	stopContainerTimeout := time.Second * 3

	return r.Client.ContainerStop(ctx, containerID, &stopContainerTimeout)
}
