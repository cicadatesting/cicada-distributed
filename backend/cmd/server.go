package cmd

import (
	"context"
	"fmt"

	"github.com/cicadatesting/backend/api"
	"github.com/cicadatesting/backend/pkg/application"
	"github.com/cicadatesting/backend/pkg/types"
	"github.com/golang/protobuf/ptypes/empty"
	"github.com/sirupsen/logrus"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/wrapperspb"

	_ "google.golang.org/grpc/encoding/gzip"
)

type Server struct {
	api.UnimplementedBackendServer
	backend *application.Backend
}

func NewServer(backend *application.Backend) *Server {
	return &Server{backend: backend}
}

func (s *Server) CreateTest(ctx context.Context, in *api.CreateTestRequest) (*api.CreateTestResponse, error) {
	testID, err := s.backend.CreateTest(
		in.GetBackendAddress(),
		in.GetSchedulingMetadata(),
		in.GetTags(),
		in.GetEnv(),
	)

	if err != nil {
		logrus.Error(err)
	}

	return &api.CreateTestResponse{TestID: testID}, err
}

func (s *Server) CreateScenario(ctx context.Context, in *api.CreateScenarioRequest) (*api.CreateScenarioResponse, error) {
	scenarioID, err := s.backend.CreateScenario(
		in.GetTestID(),
		in.GetScenarioName(),
		in.GetContext(),
		int(in.GetUsersPerInstance()),
		in.GetTags(),
	)

	if err != nil {
		logrus.Error(err)
	}

	return &api.CreateScenarioResponse{ScenarioID: scenarioID}, err
}

func (s *Server) CreateUsers(ctx context.Context, in *api.CreateUsersRequest) (*api.CreateUsersResponse, error) {
	userManagerIDs, err := s.backend.CreateUsers(in.GetScenarioID(), in.GetTestID(), int(in.GetAmount()))

	if err != nil {
		logrus.Error(err)
	}

	return &api.CreateUsersResponse{UserManagerIDs: userManagerIDs}, err
}

func (s *Server) StopUsers(ctx context.Context, in *api.StopUsersRequest) (*empty.Empty, error) {
	err := s.backend.StopUsers(in.GetScenarioID(), int(in.GetAmount()))

	if err != nil {
		logrus.Error(err)
	}

	return &empty.Empty{}, err
}

func (s *Server) CleanTestInstances(ctx context.Context, in *api.CleanTestInstancesRequest) (*empty.Empty, error) {
	err := s.backend.CleanTestInstances(in.GetTestID())

	if err != nil {
		logrus.Error(err)
	}

	return &empty.Empty{}, err
}

func (s *Server) CheckTestInstance(ctx context.Context, in *api.CheckTestInstanceRequest) (*api.CheckTestInstanceResponse, error) {
	running, err := s.backend.CheckTestInstance(in.GetTestID(), in.GetInstanceID())

	if err != nil {
		logrus.Error(err)
		return &api.CheckTestInstanceResponse{}, err
	}

	return &api.CheckTestInstanceResponse{Running: running}, nil
}

func (s *Server) AddTestEvent(ctx context.Context, in *api.AddEventRequest) (*empty.Empty, error) {
	err := s.backend.AddTestEvent(
		in.GetId(),
		in.GetEvent().GetKind(),
		in.GetEvent().GetPayload(),
	)

	if err != nil {
		logrus.Error("Error adding test events:", err)
		return nil, fmt.Errorf("Error adding test events: %v", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetTestEvents(ctx context.Context, in *api.GetEventsRequest) (*api.Events, error) {
	events, err := s.backend.GetTestEvents(in.GetId())

	if err != nil {
		logrus.Error("Error getting test events:", err)
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

func (s *Server) AddUserResults(ctx context.Context, in *api.AddUserResultsRequest) (*empty.Empty, error) {
	err := s.backend.AddUserResults(in.GetUserManagerID(), in.GetResults())

	if err != nil {
		logrus.Error("Error adding user result:", err)
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

	err := s.backend.SetScenarioResult(
		in.GetScenarioID(),
		output,
		exception,
		in.GetLogs(),
		in.GetTimeTaken(),
		in.GetSucceeded(),
		in.GetFailed(),
	)

	if err != nil {
		logrus.Error("Error adding scenario result:", err)
		return nil, fmt.Errorf("Error adding scenario result: %v", err)
	}

	return &empty.Empty{}, nil
}

func (s *Server) MoveUserResults(ctx context.Context, in *api.MoveUserResultsRequest) (*api.MoveUserResultsResponse, error) {
	limit := int(in.GetLimit())

	if limit < 1 {
		limit = 500
	}

	results, err := s.backend.MoveUserResults(in.GetScenarioID(), limit)

	if err != nil {
		logrus.Error("Error getting user results:", err)
		return nil, fmt.Errorf("Error getting user results: %v", err)
	}

	response := api.MoveUserResultsResponse{
		Results: results,
	}

	return &response, nil
}

func (s *Server) MoveScenarioResult(ctx context.Context, in *api.MoveScenarioResultRequest) (*api.MoveScenarioResultResponse, error) {
	result, err := s.backend.MoveScenarioResult(in.GetScenarioID())

	if err == types.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Result for scenario %s not found", in.GetScenarioID()))
	}

	if err != nil {
		logrus.Error("Error moving scenario result:", err)
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
	err := s.backend.DistributeWork(in.GetScenarioID(), int(in.GetAmount()))

	if err != nil {
		logrus.Error("Error distributing work:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetUserWork(ctx context.Context, in *api.GetUserWorkRequest) (*api.GetUserWorkResponse, error) {
	work, err := s.backend.GetUserWork(in.GetUserManagerID())

	if err != nil {
		logrus.Error("Error getting user work:", err)
	}

	return &api.GetUserWorkResponse{Work: int32(work)}, err
}

func (s *Server) AddUserEvent(ctx context.Context, in *api.AddEventRequest) (*empty.Empty, error) {
	err := s.backend.AddUserEvent(
		in.GetId(),
		in.GetEvent().GetKind(),
		in.GetEvent().GetPayload(),
	)

	if err != nil {
		logrus.Error("Error adding user event:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetUserEvents(ctx context.Context, in *api.GetEventsRequest) (*api.Events, error) {
	events, err := s.backend.GetUserEvents(in.GetId(), in.GetKind())

	if err != nil {
		logrus.Error("Error getting user events:", err)
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
	err := s.backend.AddMetric(in.GetScenarioID(), in.GetName(), in.GetValue())

	if err != nil {
		logrus.Error("Error adding metric:", err)
	}

	return &empty.Empty{}, err
}

func (s *Server) GetMetricTotal(ctx context.Context, in *api.GetMetricRequest) (*api.MetricTotalResponse, error) {
	total, err := s.backend.GetMetricTotal(in.GetScenarioID(), in.GetName())

	if err == types.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	if err != nil {
		logrus.Error("Error getting metric total:", err)
	}

	return &api.MetricTotalResponse{Total: total}, err
}

func (s *Server) GetLastMetric(ctx context.Context, in *api.GetMetricRequest) (*api.LastMetricResponse, error) {
	last, err := s.backend.GetLastMetric(in.GetScenarioID(), in.GetName())

	if err == types.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	return &api.LastMetricResponse{Last: last}, err
}

func (s *Server) GetMetricRate(ctx context.Context, in *api.GetMetricRateRequest) (*api.MetricRateResponse, error) {
	rate, err := s.backend.GetRate(in.GetScenarioID(), in.GetName(), in.GetSplitPoint())

	if err == types.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	return &api.MetricRateResponse{Percentage: rate}, err
}

func (s *Server) GetMetricStatistics(ctx context.Context, in *api.GetMetricRequest) (*api.MetricStatisticsResponse, error) {
	stats, err := s.backend.GetMetricStatistics(in.GetScenarioID(), in.GetName())

	if err == types.NotFound {
		return nil, status.Error(codes.NotFound, fmt.Sprintf("Metric for %s not found", in.GetName()))
	}

	if err != nil {
		logrus.Error("Error getting metric statistics:", err)
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
