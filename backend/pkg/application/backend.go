package application

import "fmt"

type Backend struct {
	datastore Datastore
	scheduler Scheduler
}

func NewBackend(datastore Datastore, scheduler Scheduler) *Backend {
	return &Backend{datastore, scheduler}
}

type Datastore interface {
	CreateTest(backendAddress, schedulingMetadata string, tags []string) (string, error)
	GetTest(testID string) (*Test, error)
	CreateScenario(testID, scenarioName, context string, usersPerInstance int, tags []string) (string, error)
	GetScenario(scenarioID string) (*Scenario, error)
	CreateUsers(scenarioID string, amount int) ([]string, error)
	StopUsers(scenarioID string, amount int) ([]string, error)
	AddTestEvent(testID, kind string, payload []byte) error
	GetTestEvents(testID string) ([]Event, error)
	AddUserResults(userManagerID string, results [][]byte) error
	SetScenarioResult(
		scenarioID string,
		output *string,
		exception *string,
		logs string,
		timeTaken float64,
		succeeded int32,
		failed int32,
	) error
	MoveUserResults(scenarioID string, limit int) ([][]byte, error)
	MoveScenarioResult(scenarioID string) (*ScenarioResult, error)
	DistributeWork(scenarioID string, amount int) error
	GetUserWork(userManagerID string) (int, error)
	AddUserEvent(scenarioID, kind string, payload []byte) error
	GetUserEvents(userManagerID, kind string) ([]Event, error)
	AddMetric(scenarioID, name string, value float64) error
	GetLastMetric(scenarioID, name string) (float64, error)
	GetMetricStatistics(scenarioID, name string) (*MetricStatistics, error)
	GetMetricTotal(scenarioID, name string) (float64, error)
	GetRate(scenarioID, name string, splitPoint float64) (float64, error)
}

type Scheduler interface {
	CreateTest(testID, backendAddress, schedulingMetadata string, tags []string) error
	CreateScenario(
		testID,
		scenarioID,
		scenarioName,
		backendAddress,
		schedulingMetadata,
		encodedContext string,
	) error
	CreateUserManagers(
		userManagerIDs []string,
		testID, scenarioName, backendAddress, schedulingMetadata, encodedContext string,
	) error
	StopUserManagers(userManagerIDs []string, schedulingMetadata string) error
	CleanTestInstances(testID, schedulingMetadata string) error
}

type Test struct {
	TestID             string
	BackendAddress     string
	SchedulingMetadata string
	Tags               []string
}

type Scenario struct {
	TestID           string
	ScenarioID       string
	ScenarioName     string
	Context          string
	UsersPerInstance int
	Tags             []string
}

type Event struct {
	Kind    string
	Payload []byte
}

type ScenarioResult struct {
	ID        string
	Output    *string
	Exception *string
	Logs      string
	Timestamp string
	TimeTaken float64
	Succeeded int32
	Failed    int32
}

type MetricStatistics struct {
	Min     float64
	Max     float64
	Median  float64
	Average float64
	Len     int64
}

func (b *Backend) CreateTest(backendAddress, schedulingMetadata string, tags []string) (string, error) {
	testID, err := b.datastore.CreateTest(backendAddress, schedulingMetadata, tags)

	if err != nil {
		return "", fmt.Errorf("Error creating test: %v", err)
	}

	err = b.scheduler.CreateTest(testID, backendAddress, schedulingMetadata, tags)

	if err != nil {
		return "", fmt.Errorf("Error starting test: %v", err)
	}

	return testID, nil
}

func (b *Backend) CreateScenario(
	testID, scenarioName, context string,
	usersPerInstance int,
	tags []string,
) (string, error) {
	test, err := b.datastore.GetTest(testID)

	if err != nil {
		return "", fmt.Errorf("Error getting test: %v", err)
	}

	scenarioID, err := b.datastore.CreateScenario(
		testID, scenarioName, context, usersPerInstance, tags,
	)

	if err != nil {
		return "", fmt.Errorf("Error creating scenario: %v", err)
	}

	err = b.scheduler.CreateScenario(
		testID,
		scenarioID,
		scenarioName,
		test.BackendAddress,
		test.SchedulingMetadata,
		context,
	)

	if err != nil {
		return "", fmt.Errorf("Error starting scenario: %v", err)
	}

	return scenarioID, nil
}

func (b *Backend) CreateUsers(scenarioID string, testID string, amount int) ([]string, error) {
	test, err := b.datastore.GetTest(testID)

	if err != nil {
		return nil, fmt.Errorf("Error getting test: %v", err)
	}

	scenario, err := b.datastore.GetScenario(scenarioID)

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario: %v", err)
	}

	userManagerIDs, err := b.datastore.CreateUsers(scenarioID, amount)

	if err != nil {
		return nil, fmt.Errorf("Error creating users: %v", err)
	}

	err = b.scheduler.CreateUserManagers(
		userManagerIDs,
		testID,
		scenario.ScenarioName,
		test.BackendAddress,
		test.SchedulingMetadata,
		scenario.Context,
	)

	if err != nil {
		return nil, fmt.Errorf("Error starting users managers: %v", err)
	}

	return userManagerIDs, nil
}

func (b *Backend) StopUsers(scenarioID string, amount int) error {
	scenario, err := b.datastore.GetScenario(scenarioID)

	if err != nil {
		return fmt.Errorf("Error getting scenario: %v", err)
	}

	test, err := b.datastore.GetTest(scenario.TestID)

	if err != nil {
		return fmt.Errorf("Error getting test: %v", err)
	}

	userManagerIDs, err := b.datastore.StopUsers(scenarioID, amount)

	if err != nil {
		return fmt.Errorf("Error sending stop user events: %v", err)
	}

	err = b.scheduler.StopUserManagers(userManagerIDs, test.SchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error stopping user managers: %v", err)
	}

	return nil
}

func (b *Backend) CleanTestInstances(testID string) error {
	test, err := b.datastore.GetTest(testID)

	if err != nil {
		return fmt.Errorf("Error getting test: %v", err)
	}

	err = b.scheduler.CleanTestInstances(testID, test.SchedulingMetadata)

	if err != nil {
		return fmt.Errorf("Error cleaning test instances: %v", err)
	}

	return nil
}

func (b *Backend) AddTestEvent(testID, kind string, payload []byte) error {
	return b.datastore.AddTestEvent(testID, kind, payload)
}

func (b *Backend) GetTestEvents(testID string) ([]Event, error) {
	return b.datastore.GetTestEvents(testID)
}

func (b *Backend) AddUserResults(userManagerID string, results [][]byte) error {
	return b.datastore.AddUserResults(userManagerID, results)
}

func (b *Backend) SetScenarioResult(
	scenarioID string,
	output *string,
	exception *string,
	logs string,
	timeTaken float64,
	succeeded int32,
	failed int32,
) error {
	return b.datastore.SetScenarioResult(scenarioID, output, exception, logs, timeTaken, succeeded, failed)
}

func (b *Backend) MoveUserResults(scenarioID string, limit int) ([][]byte, error) {
	return b.datastore.MoveUserResults(scenarioID, limit)
}

func (b *Backend) MoveScenarioResult(scenarioID string) (*ScenarioResult, error) {
	return b.datastore.MoveScenarioResult(scenarioID)
}

func (b *Backend) DistributeWork(scenarioID string, amount int) error {
	return b.datastore.DistributeWork(scenarioID, amount)
}

func (b *Backend) GetUserWork(userManagerID string) (int, error) {
	return b.datastore.GetUserWork(userManagerID)
}

func (b *Backend) AddUserEvent(scenarioID, kind string, payload []byte) error {
	return b.datastore.AddUserEvent(scenarioID, kind, payload)
}

func (b *Backend) GetUserEvents(userManagerID, kind string) ([]Event, error) {
	return b.datastore.GetUserEvents(userManagerID, kind)
}

func (b *Backend) AddMetric(scenarioID, name string, value float64) error {
	return b.datastore.AddMetric(scenarioID, name, value)
}

func (b *Backend) GetLastMetric(scenarioID, name string) (float64, error) {
	return b.datastore.GetLastMetric(scenarioID, name)
}

func (b *Backend) GetMetricStatistics(scenarioID, name string) (*MetricStatistics, error) {
	return b.datastore.GetMetricStatistics(scenarioID, name)
}

func (b *Backend) GetMetricTotal(scenarioID, name string) (float64, error) {
	return b.datastore.GetMetricTotal(scenarioID, name)
}

func (b *Backend) GetRate(scenarioID, name string, splitPoint float64) (float64, error) {
	return b.datastore.GetRate(scenarioID, name, splitPoint)
}
