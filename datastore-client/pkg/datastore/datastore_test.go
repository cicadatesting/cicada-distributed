package datastore

import (
	"testing"

	"github.com/cicadatesting/datastore-client/pkg/rediscommands"
	"github.com/stretchr/testify/mock"
)

type mockRedisClient struct {
	rediscommands.RedisCommands
	mock.Mock
}

func (mrc *mockRedisClient) ListPush(key string, values ...interface{}) error {
	mrc.Called(key, values)
	return nil
}

func TestDistributeWorkEqual(t *testing.T) {
	mrc := new(mockRedisClient)

	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)

	datastore := Datastore{rc: mrc}

	err := datastore.DistributeWork(10, []string{"abc", "def"})

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "ListPush", 2)
	mrc.AssertCalled(t, "ListPush", "abc-work", []interface{}{5})
	mrc.AssertCalled(t, "ListPush", "def-work", []interface{}{5})
}

func TestDistributeWorkUnequal(t *testing.T) {
	mrc := new(mockRedisClient)

	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)

	datastore := Datastore{rc: mrc}

	err := datastore.DistributeWork(11, []string{"abc", "def"})

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "ListPush", 2)
	mrc.AssertCalled(t, "ListPush", mock.Anything, []interface{}{5})
	mrc.AssertCalled(t, "ListPush", mock.Anything, []interface{}{6})
}

// func TestGetMetricStatistics(t *testing.T) {
// 	redisClient := redis.NewClient(&redis.Options{
// 		Addr:     fmt.Sprintf("%s:6379", "localhost"),
// 		Password: "", // no password set
// 		DB:       0,  // use default DB
// 	})

// 	redisCommands := rediscommands.NewRedisCommands(redisClient)

// 	datastore := Datastore{rc: redisCommands}

// 	scenarioID := fmt.Sprintf("scenario-%s", uuid.NewString()[:8])

// 	// add metrics
// 	datastore.AddMetric(scenarioID, 1)
// 	datastore.AddMetric(scenarioID, 2)
// 	datastore.AddMetric(scenarioID, 3)

// 	// get metric statistics
// 	stats, err := datastore.GetMetricStatistics(scenarioID)

// 	if err != nil {
// 		t.Fatal(err)
// 	}

// 	log.Println("min:", stats.Min)
// 	log.Println("max:", stats.Max)
// 	log.Println("median:", stats.Median)
// 	log.Println("avg:", stats.Average)
// 	log.Println("len:", stats.Len)

// 	count, err := datastore.GetRate(scenarioID, 2)

// 	if err != nil {
// 		t.Fatal(err)
// 	}

// 	t.Fatal(count)
// }
