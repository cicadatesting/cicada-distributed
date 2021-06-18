package cmd

import (
	"context"

	"github.com/cicadatesting/container-service/api"
	"github.com/cicadatesting/container-service/pkg"
	"github.com/docker/docker/client"
	"github.com/golang/protobuf/ptypes/empty"
)

type Server struct {
	api.UnimplementedContainerServiceServer
	dockerRunner *pkg.DockerRunner
}

func (s *Server) StartContainer(ctx context.Context, req *api.StartContainerRequest) (*empty.Empty, error) {
	var hostPort *int
	var containerPort *int
	var network *string
	var createNetwork *bool

	if req.HostPort != nil {
		hp := int(req.HostPort.Value)

		hostPort = &hp
	}

	if req.ContainerPort != nil {
		cp := int(req.ContainerPort.Value)

		containerPort = &cp
	}

	if req.Network != nil {
		network = &req.Network.Value
	}

	if req.CreateNetwork != nil {
		createNetwork = &req.CreateNetwork.Value
	}

	volumes := []pkg.DockerVolume{}

	for _, volume := range req.GetVolumes() {
		volumes = append(volumes, pkg.DockerVolume{Source: volume.Source, Destination: volume.Destination})
	}

	err := s.dockerRunner.StartContainer(
		req.GetImage(),
		req.GetName(),
		req.GetCommand(),
		req.GetLabels(),
		req.GetEnv(),
		volumes,
		hostPort,
		containerPort,
		network,
		createNetwork,
	)

	if err != nil {
		return &empty.Empty{}, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) StopContainer(ctx context.Context, req *api.StopContainerRequest) (*empty.Empty, error) {
	err := s.dockerRunner.StopContainer(req.GetContainerID())

	if err != nil {
		return &empty.Empty{}, err
	}

	return &empty.Empty{}, nil
}

func NewServer(dockerClient *client.Client) *Server {
	dockerRunner := pkg.DockerRunner{Client: dockerClient}

	return &Server{dockerRunner: &dockerRunner}
}
