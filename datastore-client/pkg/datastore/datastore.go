package datastore

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"math/rand"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/vmihailenco/msgpack/v5"
)

const NotFound = NotFoundError("Not Found")

type NotFoundError string

func (e NotFoundError) Error() string { return string(e) }

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

func userResultKey(userID string) string {
	return fmt.Sprintf("%s-results", userID)
}

func userWorkKey(userID string) string {
	return fmt.Sprintf("%s-work", userID)
}

func scenarioResultKey(scenarioID string) string {
	return fmt.Sprintf("%s-result", scenarioID)
}

func userEventKey(userID, kind string) string {
	return concatenatedKey(
		fmt.Sprintf("%s-user-events", userID),
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

type Datastore struct {
	rc IRedisCommands
}

type IRedisCommands interface {
	ListLength(key string) (int64, error)
	ListPopBytes(key string) ([]byte, error)
	ListPopInt(key string) (int, error)
	ListPush(key string, values ...interface{}) error
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
}

func NewDatastore(rc IRedisCommands) *Datastore {
	return &Datastore{rc: rc}
}

type Event struct {
	Kind    string
	Payload []byte
}

func (datastore *Datastore) addEvent(key, kind string, payload []byte) error {
	b, err := msgpack.Marshal(&Event{Kind: kind, Payload: payload})

	if err != nil {
		log.Println("Unable to parse event:", err)
		return fmt.Errorf("Unable to parse event: %v", err)
	}

	err = datastore.rc.ListPush(key, b)

	if err != nil {
		log.Println("Error adding event:", err)
		return fmt.Errorf("Error adding event: %v", err)
	}

	return nil
}

func (datastore *Datastore) getEvents(key string) ([]*Event, error) {
	len, err := datastore.rc.ListLength(key)

	if err != nil {
		log.Println("Error getting event count:", err)
		return nil, fmt.Errorf("Error getting event count: %v", err)
	}

	events := []*Event{}

	for i := int64(0); i < len; i++ {
		event := Event{}
		b, err := datastore.rc.ListPopBytes(key)

		if err != nil {
			log.Println("Error getting event:", err)
			return nil, fmt.Errorf("Error getting event: %v", err)
		}

		err = msgpack.Unmarshal(b, &event)

		if err != nil {
			log.Println("Error parsing event:", err)
			return nil, fmt.Errorf("Error parsing event: %v", err)
		}

		events = append(events, &event)
	}

	return events, nil
}

func (datastore *Datastore) AddTestEvent(testID, kind string, payload []byte) error {
	return datastore.addEvent(testEventKey(testID), kind, payload)
}

func (datastore *Datastore) GetTestEvents(testID string) ([]*Event, error) {
	return datastore.getEvents(testEventKey(testID))
}

type ScenarioResult struct {
	ID        string
	Output    *string
	Exception *string
	Logs      string
	Timestamp string
	TimeTaken float64
}

func (datastore *Datastore) AddUserResult(userID string, result []byte) error {
	// rpush into user result key
	err := datastore.rc.ListPush(userResultKey(userID), result)

	if err != nil {
		log.Println("Error adding user result:", err)
		return fmt.Errorf("Error adding user result: %v", err)
	}

	return nil
}

func (datastore *Datastore) SetScenarioResult(
	scenarioID string,
	output *string,
	exception *string,
	logs string,
	timeTaken float64,
) error {
	// set scenario result key
	// set expiration?
	// add result to test listerer queue?
	result := ScenarioResult{
		ID:        uuid.NewString(),
		Output:    output,
		Exception: exception,
		Logs:      logs,
		Timestamp: time.Now().Format(time.RFC3339),
		TimeTaken: timeTaken,
	}

	b, err := msgpack.Marshal(&result)

	if err != nil {
		log.Println("Error parsing event:", err)
		return fmt.Errorf("Error parsing event: %v", err)
	}

	err = datastore.rc.Set(scenarioResultKey(scenarioID), b, time.Hour)

	if err != nil {
		log.Println("Error adding scenario result:", err)
		return fmt.Errorf("Error adding scenario result: %v", err)
	}

	return nil
}

func (datastore *Datastore) MoveUserResults(userIDs []string, limit int) ([][]byte, error) {
	// for each user, lpop all elements of user result
	// may need to unlink key (with lock)
	results := [][]byte{}
	remaining := limit

	for _, userID := range userIDs {
		len, err := datastore.rc.ListLength(userResultKey(userID))

		if err != nil {
			log.Println("Error getting number of results:", err)
			return nil, fmt.Errorf("Error getting number of results: %v", err)
		}

		for i := int64(0); i < len; i++ {
			// Exit early if limit reached
			if remaining < 1 {
				return results, nil
			}

			result, err := datastore.rc.ListPopBytes(userResultKey(userID))

			if err != nil {
				log.Println("Error getting user result:", err)
				return nil, fmt.Errorf("Error getting user result: %v", err)
			}

			results = append(results, result)
			remaining--
		}
	}

	return results, nil
}

func (datastore *Datastore) MoveScenarioResult(scenarioID string) (*ScenarioResult, error) {
	// get value for key
	// may need to unlink key (with lock)
	result := ScenarioResult{}
	b, err := datastore.rc.GetBytes(scenarioResultKey(scenarioID))

	if err == redis.Nil {
		return nil, NotFound
	}

	if err != nil {
		log.Println("Error getting scenario result:", err)
		return nil, fmt.Errorf("Error getting scenario result: %v", err)
	}

	err = msgpack.Unmarshal(b, &result)

	if err != nil {
		log.Println("Error loading scenario result:", err)
		return nil, fmt.Errorf("Error loading scenario result: %v", err)
	}

	return &result, nil
}

func (datastore *Datastore) DistributeWork(amount int, userIDs []string) error {
	// for each user ID, determine amount of work
	// rpush work into each user work key
	numUsers := len(userIDs)

	baseWork := amount / numUsers
	withRemainingWork := amount % numUsers

	rand.Seed(time.Now().Unix())
	rand.Shuffle(numUsers, func(i, j int) {
		userIDs[i], userIDs[j] = userIDs[j], userIDs[i]
	})

	for i := 0; i < withRemainingWork; i++ {
		// NOTE: may be useful to implement in terms of user events
		err := datastore.rc.ListPush(userWorkKey(userIDs[i]), baseWork+1)

		if err != nil {
			log.Println("Error adding work:", err)
			return fmt.Errorf("Error adding work: %v", err)
		}
	}

	for j := withRemainingWork; j < numUsers; j++ {
		err := datastore.rc.ListPush(userWorkKey(userIDs[j]), baseWork)

		if err != nil {
			log.Println("Error adding work:", err)
			return fmt.Errorf("Error adding work: %v", err)
		}
	}

	return nil
}

func (datastore *Datastore) GetUserWork(userID string) (int, error) {
	// lpop all work for user work key and return total
	// may need to unlink key
	len, err := datastore.rc.ListLength(userWorkKey(userID))

	if err != nil {
		log.Println("Error getting user work count:", err)
		return 0, fmt.Errorf("Error getting user work count: %v", err)
	}

	totalWork := 0

	for i := int64(0); i < len; i++ {
		work, err := datastore.rc.ListPopInt(userWorkKey(userID))

		if err != nil {
			log.Println("Error getting user work:", err)
			return 0, fmt.Errorf("Error getting user work: %v", err)
		}

		totalWork += work
	}

	return totalWork, nil
}

func (datastore *Datastore) AddUserEvent(userID, kind string, payload []byte) error {
	return datastore.addEvent(userEventKey(userID, kind), kind, payload)
}

func (datastore *Datastore) GetUserEvents(userID, kind string) ([]*Event, error) {
	// FEATURE: limit events returned
	return datastore.getEvents(userEventKey(userID, kind))
}

func (datastore *Datastore) AddMetric(scenarioID, name string, value float64) error {
	err := datastore.rc.AddToSet(metricSetKey(scenarioID, name), value)

	if err != nil {
		log.Println("Error adding metric to set:", err)
		return fmt.Errorf("Error adding metric to set: %v", err)
	}

	err = datastore.rc.IncrementCounter(metricsIncKey(scenarioID, name), value)

	if err != nil {
		log.Println("Error adding metric count:", err)
		return fmt.Errorf("Error adding metric count: %v", err)
	}

	err = datastore.rc.Set(metricsLastKey(scenarioID, name), value, time.Hour)

	if err != nil {
		log.Println("Error setting metric:", err)
		return fmt.Errorf("Error setting metric: %v", err)
	}

	return nil
}

func (datastore *Datastore) GetLastMetric(scenarioID, name string) (float64, error) {
	last, err := datastore.rc.GetFloat(metricsLastKey(scenarioID, name))

	if err == redis.Nil {
		return 0, NotFound
	}

	if err != nil {
		log.Println("Error getting last metric:", err)
		return 0, fmt.Errorf("Error getting last metric: %v", err)
	}

	return last, nil
}

type MetricStatistics struct {
	Min     float64
	Max     float64
	Median  float64
	Average float64
	Len     int64
}

func (datastore *Datastore) GetMetricStatistics(scenarioID, name string) (*MetricStatistics, error) {
	min, err := datastore.rc.GetMin(metricSetKey(scenarioID, name))

	if err == redis.Nil {
		return nil, NotFound
	}

	if err != nil {
		log.Println("Error getting min:", err)
		return nil, fmt.Errorf("Error getting min: %v", err)
	}

	len, err := datastore.rc.GetCardinality(metricSetKey(scenarioID, name))

	if err != nil {
		log.Println("Error getting stats count:", err)
		return nil, fmt.Errorf("Error getting stats count: %v", err)
	}

	max, err := datastore.rc.GetMax(metricSetKey(scenarioID, name), len)

	if err != nil {
		log.Println("Error getting max:", err)
		return nil, fmt.Errorf("Error getting max: %v", err)
	}

	median, err := datastore.rc.GetMedian(metricSetKey(scenarioID, name), len)

	if err != nil {
		log.Println("Error getting median:", err)
		return nil, fmt.Errorf("Error getting median: %v", err)
	}

	total, err := datastore.rc.GetFloat(metricsIncKey(scenarioID, name))

	if err == redis.Nil {
		return nil, NotFound
	}

	if err != nil {
		log.Println("Error getting total:", err)
		return nil, fmt.Errorf("Error getting total: %v", err)
	}

	average := total / float64(len)

	return &MetricStatistics{
		Min:     min,
		Max:     max,
		Median:  median,
		Average: average,
		Len:     len,
	}, nil
}

func (datastore *Datastore) GetMetricTotal(scenarioID, name string) (float64, error) {
	total, err := datastore.rc.GetFloat(metricsIncKey(scenarioID, name))

	if err == redis.Nil {
		return 0, NotFound
	}

	if err != nil {
		log.Println("Error getting total:", err)
		return 0, fmt.Errorf("Error getting total: %v", err)
	}

	return total, nil
}

func (datastore *Datastore) GetRate(scenarioID, name string, splitPoint float64) (float64, error) {
	count, err := datastore.rc.RangeCount(metricSetKey(scenarioID, name), splitPoint, -1)

	if err == redis.Nil {
		return 0, NotFound
	}

	if err != nil {
		log.Println("Error getting rate:", err)
		return 0, fmt.Errorf("Error getting rate: %v", err)
	}

	len, err := datastore.rc.GetCardinality(metricSetKey(scenarioID, name))

	if err != nil {
		log.Println("Error getting stats count:", err)
		return 0, fmt.Errorf("Error getting stats count: %v", err)
	}

	return float64(count) / float64(len), nil
}
