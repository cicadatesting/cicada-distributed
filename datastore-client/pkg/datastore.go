package pkg

import (
	"context"
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"io"
	"math/rand"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/vmihailenco/msgpack/v5"
)

type Datastore struct {
	Rds RedisClient
}

type RedisClient interface {
	LLen(ctx context.Context, key string) *redis.IntCmd
	LPop(ctx context.Context, key string) *redis.StringCmd
	RPush(ctx context.Context, key string, values ...interface{}) *redis.IntCmd
	Get(ctx context.Context, key string) *redis.StringCmd
	Set(ctx context.Context, key string, value interface{}, expiration time.Duration) *redis.StatusCmd
}

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

type Event struct {
	Kind    string
	Payload []byte
}

func (datastore *Datastore) addEvent(ctx context.Context, key, kind string, payload []byte) error {
	b, err := msgpack.Marshal(&Event{Kind: kind, Payload: payload})

	if err != nil {
		return err
	}

	_, err = datastore.Rds.RPush(ctx, key, b).Result()

	return err
}

func (datastore *Datastore) getEvents(ctx context.Context, key string) ([]*Event, error) {
	len, err := datastore.Rds.LLen(ctx, key).Result()

	if err != nil {
		return nil, err
	}

	events := []*Event{}

	for i := int64(0); i < len; i++ {
		event := Event{}
		b, err := datastore.Rds.LPop(ctx, key).Bytes()

		if err != nil {
			return nil, err
		}

		err = msgpack.Unmarshal(b, &event)

		if err != nil {
			return nil, err
		}

		events = append(events, &event)
	}

	return events, nil
}

func (datastore *Datastore) AddTestEvent(ctx context.Context, testID, kind string, payload []byte) error {
	return datastore.addEvent(ctx, testEventKey(testID), kind, payload)
}

func (datastore *Datastore) GetTestEvents(ctx context.Context, testID string) ([]*Event, error) {
	return datastore.getEvents(ctx, testEventKey(testID))
}

type ScenarioResult struct {
	ID        string
	Output    *string
	Exception *string
	Logs      string
	Timestamp string
	TimeTaken float64
}

func (datastore *Datastore) AddUserResult(ctx context.Context, userID string, result []byte) error {
	// rpush into user result key
	_, err := datastore.Rds.RPush(ctx, userResultKey(userID), result).Result()

	return err
}

func (datastore *Datastore) SetScenarioResult(
	ctx context.Context,
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
		return err
	}

	_, err = datastore.Rds.Set(ctx, scenarioResultKey(scenarioID), b, time.Hour).Result()

	return err
}

func (datastore *Datastore) MoveUserResults(ctx context.Context, userIDs []string) ([][]byte, error) {
	// for each user, lpop all elements of user result
	// may need to unlink key (with lock)
	results := [][]byte{}

	for _, userID := range userIDs {
		len, err := datastore.Rds.LLen(ctx, userResultKey(userID)).Result()

		if err != nil {
			return nil, err
		}

		for i := int64(0); i < len; i++ {
			result, err := datastore.Rds.LPop(ctx, userResultKey(userID)).Bytes()

			if err != nil {
				return nil, err
			}

			results = append(results, result)
		}
	}

	return results, nil
}

func (datastore *Datastore) MoveScenarioResult(ctx context.Context, scenarioID string) (*ScenarioResult, error) {
	// get value for key
	// may need to unlink key (with lock)
	result := ScenarioResult{}
	b, err := datastore.Rds.Get(ctx, scenarioResultKey(scenarioID)).Bytes()

	if err != nil {
		return nil, err
	}

	err = msgpack.Unmarshal(b, &result)

	if err != nil {
		return nil, err
	}

	return &result, nil
}

func (datastore *Datastore) DistributeWork(ctx context.Context, amount int, userIDs []string) error {
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
		_, err := datastore.Rds.RPush(ctx, userWorkKey(userIDs[i]), baseWork+1).Result()

		if err != nil {
			return err
		}
	}

	for j := withRemainingWork; j < numUsers; j++ {
		_, err := datastore.Rds.RPush(ctx, userWorkKey(userIDs[j]), baseWork).Result()

		if err != nil {
			return err
		}
	}

	return nil
}

func (datastore *Datastore) GetUserWork(ctx context.Context, userID string) (int, error) {
	// lpop all work for user work key and return total
	// may need to unlink key
	len, err := datastore.Rds.LLen(ctx, userWorkKey(userID)).Result()

	if err != nil {
		return 0, err
	}

	totalWork := 0

	for i := int64(0); i < len; i++ {
		work, err := datastore.Rds.LPop(ctx, userWorkKey(userID)).Int()

		if err != nil {
			return 0, err
		}

		totalWork += work
	}

	return totalWork, nil
}

func (datastore *Datastore) AddUserEvent(ctx context.Context, userID, kind string, payload []byte) error {
	return datastore.addEvent(ctx, userEventKey(userID, kind), kind, payload)
}

func (datastore *Datastore) GetUserEvents(ctx context.Context, userID, kind string) ([]*Event, error) {
	return datastore.getEvents(ctx, userEventKey(userID, kind))
}
