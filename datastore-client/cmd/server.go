package cmd

import (
	"context"
	"fmt"
	"log"

	"github.com/cicadatesting/datastore-client/api"
	"github.com/cicadatesting/datastore-client/pkg/datastore"
	"github.com/cicadatesting/datastore-client/pkg/rediscommands"
	"github.com/go-redis/redis/v8"
	"github.com/golang/protobuf/ptypes/empty"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/wrapperspb"

	_ "google.golang.org/grpc/encoding/gzip"
)

type Server struct {
	api.UnimplementedDatastoreServer
	datastore *datastore.Datastore
}

func NewServer(redisClient *redis.Client) *Server {
	datastore := datastore.NewDatastore(
		rediscommands.NewRedisCommands(redisClient),
	)

	return &Server{datastore: datastore}
}

func (s *Server) AddTestEvent(ctx context.Context, in *api.AddEventRequest) (*empty.Empty, error) {
	err := s.datastore.AddTestEvent(
		in.GetId(),
		in.GetEvent().GetKind(),
		in.GetEvent().GetPayload(),
	)

	return &empty.Empty{}, err
}

func (s *Server) GetTestEvents(ctx context.Context, in *api.GetEventsRequest) (*api.Events, error) {
	events, err := s.datastore.GetTestEvents(in.GetId())

	if err != nil {
		log.Println("Error getting test events:", err)
		return nil, fmt.Errorf("Error getting test events: %v", err)
	}

	result := api.Events{
		Events: []*api.Event{},
	}

	for _, event := range events {
		result.Events = append(result.Events, &api.Event{Kind: event.Kind, Payload: event.Payload})
	}

	return &result, nil
}

func (s *Server) AddUserResult(ctx context.Context, in *api.AddUserResultRequest) (*empty.Empty, error) {
	err := s.datastore.AddUserResult(in.GetUserID(), in.GetResult())

	if err != nil {
		log.Println("Error adding user result:", err)
		return nil, fmt.Errorf("Error adding user result: %v", err)
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
		in.GetScenarioID(),
		output,
		exception,
		in.GetLogs(),
		in.GetTimeTaken(),
		in.GetSucceeded(),
		in.GetFailed(),
	)

	if err != nil {
		log.Println("Error adding scenario result:", err)
		return nil, fmt.Errorf("Error adding scenario result: %v", err)
	}

	return &empty.Empty{}, nil
}

func (s *Server) MoveUserResults(ctx context.Context, in *api.MoveUserResultsRequest) (*api.MoveUserResultsResponse, error) {
	limit := int(in.GetLimit())

	if limit < 1 {
		limit = 500
	}

	results, err := s.datastore.MoveUserResults(in.GetUserIDs(), limit)

	if err != nil {
		log.Println("Error getting user results:", err)
		return nil, fmt.Errorf("Error getting user results: %v", err)
	}

	response := api.MoveUserResultsResponse{
		Results: results,
	}

	return &response, nil
}

func (s *Server) MoveScenarioResult(ctx context.Context, in *api.MoveScenarioResultRequest) (*api.MoveScenarioResultResponse, error) {
	result, err := s.datastore.MoveScenarioResult(in.GetScenarioID())

	if err == datastore.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Result for scenario %s not found", in.GetScenarioID()))
	}

	if err != nil {
		log.Println("Error moving scenario result:", err)
		return nil, fmt.Errorf("Error moving scenario result: %v", err)
	}

	response := api.MoveScenarioResultResponse{
		Id:        result.ID,
		Output:    wrapperspb.String(*result.Output),
		Exception: wrapperspb.String(*result.Exception),
		Logs:      result.Logs,
		Timestamp: result.Timestamp,
		TimeTaken: result.TimeTaken,
		Succeeded: result.Succeeded,
		Failed:    result.Failed,
	}

	return &response, nil
}

func (s *Server) DistributeWork(ctx context.Context, in *api.DistributeWorkRequest) (*empty.Empty, error) {
	err := s.datastore.DistributeWork(int(in.GetWork()), in.GetUserIDs())

	if err != nil {
		log.Println("Error distributing work:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetUserWork(ctx context.Context, in *api.GetUserWorkRequest) (*api.GetUserWorkResponse, error) {
	work, err := s.datastore.GetUserWork(in.GetUserID())

	if err != nil {
		log.Println("Error getting user work:", err)
	}

	return &api.GetUserWorkResponse{Work: int32(work)}, err
}

func (s *Server) AddUserEvent(ctx context.Context, in *api.AddEventRequest) (*empty.Empty, error) {
	err := s.datastore.AddUserEvent(
		in.GetId(),
		in.GetEvent().GetKind(),
		in.GetEvent().GetPayload(),
	)

	if err != nil {
		log.Println("Error adding user event:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetUserEvents(ctx context.Context, in *api.GetEventsRequest) (*api.Events, error) {
	events, err := s.datastore.GetUserEvents(in.GetId(), in.GetKind())

	if err != nil {
		log.Println("Error getting user events:", err)
		return nil, fmt.Errorf("Error getting user events: %v", err)
	}

	result := api.Events{
		Events: []*api.Event{},
	}

	for _, event := range events {
		result.Events = append(result.Events, &api.Event{Kind: event.Kind, Payload: event.Payload})
	}

	return &result, nil
}

func (s *Server) AddMetric(ctx context.Context, in *api.AddMetricRequest) (*empty.Empty, error) {
	err := s.datastore.AddMetric(in.GetScenarioID(), in.GetName(), in.GetValue())

	if err != nil {
		log.Println("Error adding metric:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetMetricTotal(ctx context.Context, in *api.GetMetricRequest) (*api.MetricTotalResponse, error) {
	total, err := s.datastore.GetMetricTotal(in.GetScenarioID(), in.GetName())

	if err == datastore.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	if err != nil {
		log.Println("Error getting metric total:", err)
	}

	return &api.MetricTotalResponse{Total: total}, err
}

func (s *Server) GetLastMetric(ctx context.Context, in *api.GetMetricRequest) (*api.LastMetricResponse, error) {
	last, err := s.datastore.GetLastMetric(in.GetScenarioID(), in.GetName())

	if err == datastore.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	return &api.LastMetricResponse{Last: last}, err
}

func (s *Server) GetMetricRate(ctx context.Context, in *api.GetMetricRateRequest) (*api.MetricRateResponse, error) {
	rate, err := s.datastore.GetRate(in.GetScenarioID(), in.GetName(), in.GetSplitPoint())

	if err == datastore.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	return &api.MetricRateResponse{Percentage: rate}, err
}

func (s *Server) GetMetricStatistics(ctx context.Context, in *api.GetMetricRequest) (*api.MetricStatisticsResponse, error) {
	stats, err := s.datastore.GetMetricStatistics(in.GetScenarioID(), in.GetName())

	if err == datastore.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	if err != nil {
		log.Println("Error getting metric statistics:", err)
		return nil, err
	}

	return &api.MetricStatisticsResponse{
		Min:     stats.Min,
		Max:     stats.Max,
		Median:  stats.Median,
		Average: stats.Average,
		Len:     stats.Len,
	}, err
}
