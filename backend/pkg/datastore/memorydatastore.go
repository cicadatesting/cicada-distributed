package datastore

import (
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"math/rand"
	"time"

	"github.com/cicadatesting/backend/pkg/application"
	"github.com/cicadatesting/backend/pkg/types"
	"github.com/google/uuid"
	"github.com/vmihailenco/msgpack/v5"
)

func concatenatedKey(a string, b ...string) string {
	h := sha1.New()

	io.WriteString(h, a)

	for _, s := range b {
		io.WriteString(h, s)
	}

	return hex.EncodeToString(h.Sum(nil))
}

func testEventKey(testID string) string {
	return fmt.Sprintf("%s-test-events", testID)
}

func userResultKey(userManagerID string) string {
	return fmt.Sprintf("%s-results", userManagerID)
}

func userWorkKey(userManagerID string) string {
	return fmt.Sprintf("%s-work", userManagerID)
}

func scenarioResultKey(scenarioID string) string {
	return fmt.Sprintf("%s-result", scenarioID)
}

func scenarioUserManagersKey(scenarioID string) string {
	return fmt.Sprintf("%s-user-managers", scenarioID)
}

func scenarioBufferedWorkKey(scenarioID string) string {
	return fmt.Sprintf("%s-buffered-work", scenarioID)
}

func scenarioBufferedEventsKey(scenarioID string) string {
	return fmt.Sprintf("%s-buffered-events", scenarioID)
}

func userEventKey(userManagerID, kind string) string {
	return concatenatedKey(
		fmt.Sprintf("%s-user-events", userManagerID),
		kind,
	)
}

func metricSetKey(scenarioID, name string) string {
	return fmt.Sprintf("%s-%s-metrics-set", scenarioID, name)
}

func metricsIncKey(scenarioID, name string) string {
	return fmt.Sprintf("%s-%s-metrics-inc", scenarioID, name)
}

func metricsLastKey(scenarioID, name string) string {
	return fmt.Sprintf("%s-%s-metrics-last", scenarioID, name)
}

type MemoryDatastore struct {
	dc IDatastoreCommands
}

type IDatastoreCommands interface {
	ListLength(key string) (int64, error)
	ListPopBytes(key string) ([]byte, error)
	ListPopInt(key string) (int, error)
	ListPush(key string, value interface{}) error
	GetBytes(key string) ([]byte, error)
	GetFloat(key string) (float64, error)
	Set(key string, value interface{}, expiration time.Duration) error
	AddToSet(key string, score float64) error
	GetMin(key string) (float64, error)
	GetCardinality(key string) (int64, error)
	GetMax(key string, setLen int64) (float64, error)
	GetMedian(key string, setLen int64) (float64, error)
	IncrementCounter(key string, amount float64) error
	RangeCount(key string, min, max float64) (int64, error)
	MapSetKey(mapName, key string, value []byte) error
	MapGetKeyBytes(mapName, key string) ([]byte, error)
	MapGetKeys(mapName string) ([]string, error)
	MapKeyDelete(mapName string, key string) error
}

func NewMemoryDatastore(rc IDatastoreCommands) *MemoryDatastore {
	return &MemoryDatastore{dc: rc}
}

func (datastore *MemoryDatastore) addEvent(key, kind string, payload []byte) error {
	b, err := msgpack.Marshal(&application.Event{Kind: kind, Payload: payload})

	if err != nil {
		return fmt.Errorf("Unable to parse event: %v", err)
	}

	err = datastore.dc.ListPush(key, b)

	if err != nil {
		return fmt.Errorf("Error adding event: %v", err)
	}

	return nil
}

func (datastore *MemoryDatastore) getEvents(key string) ([]application.Event, error) {
	len, err := datastore.dc.ListLength(key)

	if err != nil {
		return nil, fmt.Errorf("Error getting event count: %v", err)
	}

	events := []application.Event{}

	for i := int64(0); i < len; i++ {
		event := application.Event{}
		b, err := datastore.dc.ListPopBytes(key)

		if err != nil {
			return nil, fmt.Errorf("Error getting event: %v", err)
		}

		err = msgpack.Unmarshal(b, &event)

		if err != nil {
			return nil, fmt.Errorf("Error parsing event: %v", err)
		}

		events = append(events, event)
	}

	return events, nil
}

func (datastore *MemoryDatastore) getUserIDs(scenarioID, userManagerID string) ([]string, error) {
	userIDs := []string{}
	userIDsBytes, err := datastore.dc.MapGetKeyBytes(scenarioUserManagersKey(scenarioID), userManagerID)

	if err != nil {
		return nil, fmt.Errorf("Error getting users under user manager %s: %v", userManagerID, err)
	}

	if userIDsBytes != nil {
		err = msgpack.Unmarshal(userIDsBytes, &userIDs)
	}

	return userIDs, nil
}

func (datastore *MemoryDatastore) CreateTest(
	backendAddress, schedulingMetadata string,
	tags []string,
	env map[string]string,
) (string, error) {
	testID := fmt.Sprintf("cicada-test-%s", uuid.NewString()[:8])

	test := application.Test{
		TestID:             testID,
		BackendAddress:     backendAddress,
		SchedulingMetadata: schedulingMetadata,
		Tags:               tags,
		Env:                env,
	}

	b, err := msgpack.Marshal(&test)

	if err != nil {
		return "", fmt.Errorf("Error marshalling test: %v", err)
	}

	err = datastore.dc.Set(testID, b, time.Hour)

	if err != nil {
		return "", fmt.Errorf("Error setting test in datastore: %v", err)
	}

	return testID, nil
}

func (datastore *MemoryDatastore) GetTest(testID string) (*application.Test, error) {
	test := application.Test{}

	b, err := datastore.dc.GetBytes(testID)

	if err == types.NotFound {
		return nil, types.NotFound
	}

	if err != nil {
		return nil, fmt.Errorf("Error getting test: %v", err)
	}

	err = msgpack.Unmarshal(b, &test)

	if err != nil {
		return nil, fmt.Errorf("Error loading test: %v", err)
	}

	return &test, nil
}

func (datastore *MemoryDatastore) CreateScenario(testID, scenarioName, context string, usersPerInstance int, tags []string) (string, error) {
	scenarioID := fmt.Sprintf("scenario-%s", uuid.NewString()[:8])

	scenario := application.Scenario{
		TestID:           testID,
		ScenarioID:       scenarioID,
		ScenarioName:     scenarioName,
		Context:          context,
		UsersPerInstance: usersPerInstance,
		Tags:             tags,
	}

	b, err := msgpack.Marshal(&scenario)

	if err != nil {
		return "", fmt.Errorf("Error marshalling scenario: %v", err)
	}

	err = datastore.dc.Set(scenarioID, b, time.Hour)

	if err != nil {
		return "", fmt.Errorf("Error setting scenario in datastore: %v", err)
	}

	return scenarioID, nil
}

func (datastore *MemoryDatastore) GetScenario(scenarioID string) (*application.Scenario, error) {
	b, err := datastore.dc.GetBytes(scenarioID)

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario: %v", err)
	}

	scenario := application.Scenario{}

	err = msgpack.Unmarshal(b, &scenario)

	if err != nil {
		return nil, fmt.Errorf("Error unmarshalling scenario: %v", err)
	}

	return &scenario, nil
}

func (datastore *MemoryDatastore) CreateUsers(scenarioID string, amount int) ([]string, error) {
	if amount < 1 {
		return []string{}, nil
	}

	// get scenario (to get users per instance)
	scenario := application.Scenario{}
	scenarioBytes, err := datastore.dc.GetBytes(scenarioID)

	if err == types.NotFound {
		return nil, types.NotFound
	}

	if err != nil {
		return nil, fmt.Errorf("Error getting test: %v", err)
	}

	err = msgpack.Unmarshal(scenarioBytes, &scenario)

	if err != nil {
		return nil, fmt.Errorf("Error loading test: %v", err)
	}

	// get user managers for scenario
	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	usersToCreate := map[string][]string{}
	newUserManagers := []string{}
	remainingUsers := amount

	// attempt to fill existing user managers
	for _, userManagerID := range userManagers {
		userIDs, err := datastore.getUserIDs(scenarioID, userManagerID)

		if err != nil {
			return nil, err
		}

		availableUsers := scenario.UsersPerInstance - len(userIDs)

		for remainingUsers > 0 && availableUsers > 0 {
			newUserID := fmt.Sprintf("user-%s", uuid.NewString()[:8])

			usersToCreate[userManagerID] = append(usersToCreate[userManagerID], newUserID)
			userIDs = append(userIDs, newUserID)

			remainingUsers--
			availableUsers--
		}

		b, err := msgpack.Marshal(userIDs)

		if err != nil {
			return nil, fmt.Errorf("Error marshalling user ids: %v", err)
		}

		err = datastore.dc.MapSetKey(scenarioUserManagersKey(scenarioID), userManagerID, b)

		if err != nil {
			return nil, fmt.Errorf("Error adding user ids: %v", err)
		}
	}

	// determine new user managers
	for remainingUsers > 0 {
		userManagerID := fmt.Sprintf("user-manager-%s", uuid.NewString()[:8])
		numUsersForManager := math.Min(float64(scenario.UsersPerInstance), float64(remainingUsers))
		userIDs := []string{}

		for i := 0; i < int(numUsersForManager); i++ {
			userIDs = append(userIDs, fmt.Sprintf("user-%s", uuid.NewString()[:8]))
		}

		usersToCreate[userManagerID] = userIDs
		newUserManagers = append(newUserManagers, userManagerID)

		b, err := msgpack.Marshal(userIDs)

		if err != nil {
			return nil, fmt.Errorf("Error marshalling user ids: %v", err)
		}

		err = datastore.dc.MapSetKey(scenarioUserManagersKey(scenarioID), userManagerID, b)

		if err != nil {
			return nil, fmt.Errorf("Error setting user manager: %v", err)
		}

		remainingUsers -= int(numUsersForManager)
	}

	// send events for new users
	for userManagerID, userIDs := range usersToCreate {
		payload := map[string][]string{"IDs": userIDs}

		b, err := json.Marshal(payload)

		if err != nil {
			return nil, fmt.Errorf("Error sending start users message: %v", err)
		}

		err = datastore.addEvent(userEventKey(userManagerID, "START_USERS"), "START_USERS", b)

		if err != nil {
			return nil, fmt.Errorf("Error adding user events for user manager %s: %v", userManagerID, err)
		}
	}

	// store / send buffered work
	err = datastore.distributeBufferedWork(scenarioID)

	if err != nil {
		return nil, fmt.Errorf("Error distributing buffered work: %v", err)
	}

	err = datastore.distributeBufferedUserEvents(scenarioID)

	if err != nil {
		return nil, fmt.Errorf("Error distributing buffered user events: %v", err)
	}

	return newUserManagers, nil
}

func (datastore *MemoryDatastore) StopUsers(scenarioID string, amount int) ([]string, error) {
	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	userManagersToStop := []string{}

	remaining := amount

	for _, userManagerID := range userManagers {
		if remaining < 1 {
			break
		}

		userIDs, err := datastore.getUserIDs(scenarioID, userManagerID)

		if err != nil {
			return nil, err
		}

		numUsersToRemove := math.Min(float64(remaining), float64(len(userIDs)))
		remainingUsers := userIDs[int(numUsersToRemove):]

		// send stop events for users to remove
		payload := map[string][]string{"IDs": userIDs[:int(numUsersToRemove)]}

		b, err := json.Marshal(&payload)

		if err != nil {
			return nil, fmt.Errorf("Error sending stop users message: %v", err)
		}

		err = datastore.addEvent(userEventKey(userManagerID, "STOP_USERS"), "STOP_USERS", b)

		if err != nil {
			return nil, fmt.Errorf("Error adding user events for user manager %s: %v", userManagerID, err)
		}

		// Delete user managers or send stop user events
		if len(remainingUsers) < 1 {
			err := datastore.dc.MapKeyDelete(scenarioUserManagersKey(scenarioID), userManagerID)

			if err != nil {
				return nil, fmt.Errorf("Error removing user manager key: %v", err)
			}

			userManagersToStop = append(userManagersToStop, userManagerID)
		} else {
			b, err := msgpack.Marshal(remainingUsers)

			if err != nil {
				return nil, fmt.Errorf("Error marshalling user ids: %v", err)
			}

			err = datastore.dc.MapSetKey(scenarioUserManagersKey(scenarioID), userManagerID, b)

			if err != nil {
				return nil, fmt.Errorf("Error setting user manager: %v", err)
			}
		}

		remaining -= int(numUsersToRemove)
	}

	return userManagersToStop, nil
}

func (datastore *MemoryDatastore) AddTestEvent(testID, kind string, payload []byte) error {
	return datastore.addEvent(testEventKey(testID), kind, payload)
}

func (datastore *MemoryDatastore) GetTestEvents(testID string) ([]application.Event, error) {
	return datastore.getEvents(testEventKey(testID))
}

func (datastore *MemoryDatastore) AddUserResults(userManagerID string, results [][]byte) error {
	// rpush into user result key
	for _, result := range results {
		err := datastore.dc.ListPush(userResultKey(userManagerID), result)

		if err != nil {
			return fmt.Errorf("Error adding user result: %v", err)
		}
	}

	return nil
}

func (datastore *MemoryDatastore) SetScenarioResult(
	scenarioID string,
	output *string,
	exception *string,
	logs string,
	timeTaken float64,
	succeeded int32,
	failed int32,
) error {
	// set scenario result key
	// set expiration?
	// add result to test listerer queue?
	result := application.ScenarioResult{
		ID:        uuid.NewString(),
		Output:    output,
		Exception: exception,
		Logs:      logs,
		Timestamp: time.Now().Format(time.RFC3339),
		TimeTaken: timeTaken,
		Succeeded: succeeded,
		Failed:    failed,
	}

	b, err := msgpack.Marshal(&result)

	if err != nil {
		return fmt.Errorf("Error parsing event: %v", err)
	}

	err = datastore.dc.Set(scenarioResultKey(scenarioID), b, time.Hour)

	if err != nil {
		return fmt.Errorf("Error adding scenario result: %v", err)
	}

	return nil
}

func (datastore *MemoryDatastore) MoveUserResults(scenarioID string, limit int) ([][]byte, error) {
	// for each user, lpop all elements of user result
	// may need to unlink key (with lock)
	results := [][]byte{}
	remaining := limit

	// get user manager ids for scenario
	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	for _, userManagerID := range userManagers {
		len, err := datastore.dc.ListLength(userResultKey(userManagerID))

		if err != nil {
			return nil, fmt.Errorf("Error getting number of results: %v", err)
		}

		for i := int64(0); i < len; i++ {
			// Exit early if limit reached
			if remaining < 1 {
				return results, nil
			}

			result, err := datastore.dc.ListPopBytes(userResultKey(userManagerID))

			if err != nil {
				return nil, fmt.Errorf("Error getting user result: %v", err)
			}

			results = append(results, result)
			remaining--
		}
	}

	return results, nil
}

func (datastore *MemoryDatastore) MoveScenarioResult(scenarioID string) (*application.ScenarioResult, error) {
	// get value for key
	// may need to unlink key (with lock)
	result := application.ScenarioResult{}
	b, err := datastore.dc.GetBytes(scenarioResultKey(scenarioID))

	if err == types.NotFound {
		return nil, types.NotFound
	}

	if err != nil {
		return nil, fmt.Errorf("Error getting scenario result: %v", err)
	}

	err = msgpack.Unmarshal(b, &result)

	if err != nil {
		return nil, fmt.Errorf("Error loading scenario result: %v", err)
	}

	return &result, nil
}

func (datastore *MemoryDatastore) DistributeWork(scenarioID string, amount int) error {
	// for each user ID, determine amount of work
	// rpush work into each user work key
	// Get users for scenario
	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if err != nil {
		return fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	numUsers := len(userManagers)

	if numUsers < 1 {
		err := datastore.dc.ListPush(scenarioBufferedWorkKey(scenarioID), amount)

		if err != nil {
			return fmt.Errorf("Error adding buffered work: %v", err)
		}

		return nil
	}

	// shuffle user managers
	baseWork := amount / numUsers
	withRemainingWork := amount % numUsers

	rand.Seed(time.Now().Unix())
	rand.Shuffle(numUsers, func(i, j int) {
		userManagers[i], userManagers[j] = userManagers[j], userManagers[i]
	})

	// add work to each user manager
	for i := 0; i < withRemainingWork; i++ {
		// NOTE: may be useful to implement in terms of user events
		err := datastore.dc.ListPush(userWorkKey(userManagers[i]), baseWork+1)

		if err != nil {
			return fmt.Errorf("Error adding work: %v", err)
		}
	}

	for j := withRemainingWork; j < numUsers; j++ {
		err := datastore.dc.ListPush(userWorkKey(userManagers[j]), baseWork)

		if err != nil {
			return fmt.Errorf("Error adding work: %v", err)
		}
	}

	return nil
}

func (datastore *MemoryDatastore) distributeBufferedWork(scenarioID string) error {
	len, err := datastore.dc.ListLength(scenarioBufferedWorkKey(scenarioID))

	if err != nil {
		return fmt.Errorf("Error getting buffered work list length: %v", err)
	}

	totalWork := 0

	for i := int64(0); i < len; i++ {
		work, err := datastore.dc.ListPopInt(scenarioBufferedWorkKey(scenarioID))

		if err != nil {
			return fmt.Errorf("Error getting user work: %v", err)
		}

		totalWork += work
	}

	if totalWork > 0 {
		return datastore.DistributeWork(scenarioID, totalWork)
	}

	return nil
}

func (datastore *MemoryDatastore) GetUserWork(userManagerID string) (int, error) {
	// lpop all work for user work key and return total
	// may need to unlink key
	len, err := datastore.dc.ListLength(userWorkKey(userManagerID))

	if err != nil {
		return 0, fmt.Errorf("Error getting user work count: %v", err)
	}

	totalWork := 0

	for i := int64(0); i < len; i++ {
		work, err := datastore.dc.ListPopInt(userWorkKey(userManagerID))

		if err != nil {
			return 0, fmt.Errorf("Error getting user work: %v", err)
		}

		totalWork += work
	}

	return totalWork, nil
}

func (datastore *MemoryDatastore) GetUserEvents(userManagerID, kind string) ([]application.Event, error) {
	// FEATURE: limit events returned
	return datastore.getEvents(userEventKey(userManagerID, kind))
}

func (datastore *MemoryDatastore) AddUserEvent(scenarioID, kind string, payload []byte) error {
	// for each user manager in scenario, send event
	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if len(userManagers) < 1 {
		err := datastore.dc.ListPush(scenarioBufferedEventsKey(scenarioID), payload)

		if err != nil {
			return fmt.Errorf("Error adding buffered work: %v", err)
		}
	}

	if err != nil {
		return fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	for _, userManagerID := range userManagers {
		err := datastore.addEvent(userEventKey(userManagerID, kind), kind, payload)

		if err != nil {
			return fmt.Errorf("Error adding user events for user manager %s: %v", userManagerID, err)
		}
	}

	return nil
}

func (datastore *MemoryDatastore) distributeBufferedUserEvents(scenarioID string) error {
	len, err := datastore.dc.ListLength(scenarioBufferedEventsKey(scenarioID))

	if err != nil {
		return fmt.Errorf("Error getting buffered work list length: %v", err)
	}

	events := []application.Event{}

	for i := int64(0); i < len; i++ {
		event := application.Event{}
		b, err := datastore.dc.ListPopBytes(scenarioBufferedEventsKey(scenarioID))

		if err != nil {
			return fmt.Errorf("Error getting event: %v", err)
		}

		err = msgpack.Unmarshal(b, &event)

		if err != nil {
			return fmt.Errorf("Error parsing event: %v", err)
		}

		events = append(events, event)
	}

	userManagers, err := datastore.dc.MapGetKeys(scenarioUserManagersKey(scenarioID))

	if err != nil {
		return fmt.Errorf("Error getting scenario user manager: %v", err)
	}

	for _, userManagerID := range userManagers {
		for _, event := range events {
			err := datastore.addEvent(userEventKey(userManagerID, event.Kind), event.Kind, event.Payload)

			if err != nil {
				return fmt.Errorf("Error adding user events for user manager %s: %v", userManagerID, err)
			}
		}
	}

	return nil
}

func (datastore *MemoryDatastore) AddMetric(scenarioID, name string, value float64) error {
	err := datastore.dc.AddToSet(metricSetKey(scenarioID, name), value)

	if err != nil {
		return fmt.Errorf("Error adding metric to set: %v", err)
	}

	err = datastore.dc.IncrementCounter(metricsIncKey(scenarioID, name), value)

	if err != nil {
		return fmt.Errorf("Error adding metric count: %v", err)
	}

	err = datastore.dc.Set(metricsLastKey(scenarioID, name), value, time.Hour)

	if err != nil {
		return fmt.Errorf("Error setting metric: %v", err)
	}

	return nil
}

func (datastore *MemoryDatastore) GetLastMetric(scenarioID, name string) (float64, error) {
	last, err := datastore.dc.GetFloat(metricsLastKey(scenarioID, name))

	if err == types.NotFound {
		return 0, types.NotFound
	}

	if err != nil {
		return 0, fmt.Errorf("Error getting last metric: %v", err)
	}

	return last, nil
}

func (datastore *MemoryDatastore) GetMetricStatistics(scenarioID, name string) (*application.MetricStatistics, error) {
	min, err := datastore.dc.GetMin(metricSetKey(scenarioID, name))

	if err == types.NotFound {
		return nil, types.NotFound
	}

	if err != nil {
		return nil, fmt.Errorf("Error getting min: %v", err)
	}

	len, err := datastore.dc.GetCardinality(metricSetKey(scenarioID, name))

	if err != nil {
		return nil, fmt.Errorf("Error getting stats count: %v", err)
	}

	max, err := datastore.dc.GetMax(metricSetKey(scenarioID, name), len)

	if err != nil {
		return nil, fmt.Errorf("Error getting max: %v", err)
	}

	median, err := datastore.dc.GetMedian(metricSetKey(scenarioID, name), len)

	if err != nil {
		return nil, fmt.Errorf("Error getting median: %v", err)
	}

	total, err := datastore.dc.GetFloat(metricsIncKey(scenarioID, name))

	if err == types.NotFound {
		return nil, types.NotFound
	}

	if err != nil {
		return nil, fmt.Errorf("Error getting total: %v", err)
	}

	average := total / float64(len)

	return &application.MetricStatistics{
		Min:     min,
		Max:     max,
		Median:  median,
		Average: average,
		Len:     len,
	}, nil
}

func (datastore *MemoryDatastore) GetMetricTotal(scenarioID, name string) (float64, error) {
	total, err := datastore.dc.GetFloat(metricsIncKey(scenarioID, name))

	if err == types.NotFound {
		return 0, types.NotFound
	}

	if err != nil {
		return 0, fmt.Errorf("Error getting total: %v", err)
	}

	return total, nil
}

func (datastore *MemoryDatastore) GetRate(scenarioID, name string, splitPoint float64) (float64, error) {
	count, err := datastore.dc.RangeCount(metricSetKey(scenarioID, name), splitPoint, -1)

	if err == types.NotFound {
		return 0, types.NotFound
	}

	if err != nil {
		return 0, fmt.Errorf("Error getting rate: %v", err)
	}

	len, err := datastore.dc.GetCardinality(metricSetKey(scenarioID, name))

	if err != nil {
		return 0, fmt.Errorf("Error getting stats count: %v", err)
	}

	return float64(count) / float64(len), nil
}
