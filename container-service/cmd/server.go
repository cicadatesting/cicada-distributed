package cmd

import (
	"context"

	"github.com/cicadatesting/container-service/api"
	"github.com/golang/protobuf/ptypes/empty"
)

type Server struct {
	api.UnimplementedContainerServiceServer
	handler Handler
}

func (s *Server) StartContainer(ctx context.Context, req *api.StartContainerRequest) (*empty.Empty, error) {
	err := s.handler.StartContainer(req)

	if err != nil {
		return &empty.Empty{}, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) StopContainer(ctx context.Context, req *api.StopContainerRequest) (*empty.Empty, error) {
	err := s.handler.StopContainer(req)

	if err != nil {
		return &empty.Empty{}, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) StopContainers(ctx context.Context, req *api.StopContainersRequest) (*empty.Empty, error) {
	err := s.handler.StopContainers(req)

	if err != nil {
		return &empty.Empty{}, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) ContainerRunning(ctx context.Context, req *api.DescribeContainerRequest) (*api.ContainerRunningResponse, error) {
	running := s.handler.ContainerRunning(req)

	return &api.ContainerRunningResponse{Running: running}, nil
}

func NewServer(handler Handler) *Server {
	return &Server{handler: handler}
}
