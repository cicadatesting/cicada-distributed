package cmd

import (
	"context"
	"fmt"

	"github.com/cicadatesting/datastore-client/api"
	"github.com/cicadatesting/datastore-client/pkg"
	"github.com/go-redis/redis/v8"
	"github.com/golang/protobuf/ptypes/empty"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/wrapperspb"
)

type Server struct {
	api.UnimplementedDatastoreServer
	datastore *pkg.Datastore
}

func (s *Server) AddUserResult(ctx context.Context, in *api.AddUserResultRequest) (*empty.Empty, error) {
	err := s.datastore.AddUserResult(context.Background(), in.GetUserID(), in.GetResult())

	if err != nil {
		return nil, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) SetScenarioResult(ctx context.Context, in *api.SetScenarioResultRequest) (*empty.Empty, error) {
	var output *string
	var exception *string

	if in.GetOutput() != nil {
		output = &in.GetOutput().Value
	}

	if in.GetException() != nil {
		exception = &in.GetException().Value
	}

	err := s.datastore.SetScenarioResult(
		context.Background(),
		in.GetScenarioID(),
		output,
		exception,
		in.GetLogs(),
		in.GetTimeTaken(),
	)

	if err != nil {
		return nil, err
	}

	return &empty.Empty{}, nil
}

func (s *Server) MoveUserResults(ctx context.Context, in *api.MoveUserResultsRequest) (*api.MoveUserResultsResponse, error) {
	results, err := s.datastore.MoveUserResults(context.Background(), in.GetUserIDs())

	if err != nil {
		return nil, err
	}

	response := api.MoveUserResultsResponse{
		Results: results,
	}

	return &response, nil
}

func (s *Server) MoveScenarioResult(ctx context.Context, in *api.MoveScenarioResultRequest) (*api.MoveScenarioResultResponse, error) {
	result, err := s.datastore.MoveScenarioResult(context.Background(), in.GetScenarioID())

	if err == redis.Nil {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Result for scenario %s not found", in.GetScenarioID()))
	}

	if err != nil {
		return nil, err
	}

	response := api.MoveScenarioResultResponse{
		Id:        result.ID,
		Output:    wrapperspb.String(*result.Output),
		Exception: wrapperspb.String(*result.Exception),
		Logs:      result.Logs,
		Timestamp: result.Timestamp,
		TimeTaken: result.TimeTaken,
	}

	return &response, nil
}

func (s *Server) DistributeWork(ctx context.Context, in *api.DistributeWorkRequest) (*empty.Empty, error) {
	err := s.datastore.DistributeWork(context.Background(), int(in.GetWork()), in.GetUserIDs())

	return &empty.Empty{}, err
}

func (s *Server) GetUserWork(ctx context.Context, in *api.GetUserWorkRequest) (*api.GetUserWorkResponse, error) {
	work, err := s.datastore.GetUserWork(context.Background(), in.GetUserID())

	return &api.GetUserWorkResponse{Work: int32(work)}, err
}

func NewServer(redisClient *redis.Client) *Server {
	datastore := pkg.Datastore{Rds: redisClient}

	return &Server{datastore: &datastore}
}
