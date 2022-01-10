package datastore

import (
	"fmt"
	"testing"

	"github.com/cicadatesting/backend/pkg/application"
	"github.com/cicadatesting/backend/pkg/rediscommands"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/vmihailenco/msgpack/v5"
)

type mockRedisUsersClient struct {
	rediscommands.RedisCommands
	mock.Mock
}

func (mrc *mockRedisUsersClient) GetBytes(scenarioID string) ([]byte, error) {
	args := mrc.Called(scenarioID)
	return args.Get(0).([]byte), args.Error(1)
}

func (mrc *mockRedisUsersClient) MapGetKeys(mapName string) ([]string, error) {
	args := mrc.Called(mapName)
	return args.Get(0).([]string), args.Error(1)
}

func (mrc *mockRedisUsersClient) MapGetKeyBytes(mapName string, key string) ([]byte, error) {
	args := mrc.Called(mapName, key)
	return args.Get(0).([]byte), args.Error(1)
}

func (mrc *mockRedisUsersClient) MapSetKey(mapName, key string, value []byte) error {
	args := mrc.Called(mapName, key, value)
	return args.Error(0)
}

func (mrc *mockRedisUsersClient) ListPush(key string, value interface{}) error {
	args := mrc.Called(key, value)
	return args.Error(0)
}

func (mrc *mockRedisUsersClient) MapKeyDelete(mapName, key string) error {
	args := mrc.Called(mapName, key)
	return args.Error(0)
}

func (mrc *mockRedisUsersClient) ListLength(key string) (int64, error) {
	args := mrc.Called(key)
	return args.Get(0).(int64), args.Error(1)
}

func (mrc *mockRedisUsersClient) ListPopInt(key string) (int, error) {
	args := mrc.Called(key)
	return args.Int(0), args.Error(1)
}

func (mrc *mockRedisUsersClient) ListPopBytes(key string) ([]byte, error) {
	args := mrc.Called(key)
	return args.Get(0).([]byte), args.Error(1)
}

func scenarioToBytes(scenario *application.Scenario) []byte {
	b, _ := msgpack.Marshal(scenario)

	return b
}

func generateUserIDs(amount int) []byte {
	userIDs := []string{}

	for i := 0; i < amount; i++ {
		userIDs = append(userIDs, fmt.Sprintf("user-%s", uuid.NewString()[:8]))
	}

	b, _ := msgpack.Marshal(userIDs)

	return b
}

func TestCreateUsersNew(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	scenario := application.Scenario{
		UsersPerInstance: 50,
	}

	mrc.On("GetBytes", mock.Anything).Return(scenarioToBytes(&scenario), nil)
	mrc.On("MapGetKeys", mock.Anything).Return([]string{}, nil)
	mrc.On("MapSetKey", mock.Anything, mock.Anything, mock.Anything).Return(nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)
	mrc.On("ListLength", mock.Anything).Return(int64(0), nil)

	datastore := RedisDatastore{rc: mrc}

	userManagerIDs, err := datastore.CreateUsers("123", 60)

	if err != nil {
		t.Errorf("TestCreateUsersNew failed: %v", err)
	}

	assert.Equal(t, 2, len(userManagerIDs))
	mrc.AssertNumberOfCalls(t, "ListPush", 2)
}

func TestCreateUsersExisting(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	scenario := application.Scenario{
		UsersPerInstance: 50,
	}

	mrc.On("GetBytes", mock.Anything).Return(scenarioToBytes(&scenario), nil)
	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc"}, nil)
	mrc.On("MapSetKey", mock.Anything, mock.Anything, mock.Anything).Return(nil)
	mrc.On("MapGetKeyBytes", mock.Anything, mock.Anything).Return(generateUserIDs(40), nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)
	mrc.On("ListLength", mock.Anything).Return(int64(0), nil)

	datastore := RedisDatastore{rc: mrc}

	userManagerIDs, err := datastore.CreateUsers("123", 60)

	if err != nil {
		t.Errorf("TestCreateUsersNew failed: %v", err)
	}

	assert.Equal(t, 1, len(userManagerIDs))
	mrc.AssertNumberOfCalls(t, "ListPush", 2)
}

func TestStopUsers(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	abcUsers := []string{"1", "2"}
	defUsers := []string{"3", "4", "5"}

	b1, _ := msgpack.Marshal(abcUsers)
	b2, _ := msgpack.Marshal(defUsers)

	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc", "def"}, nil)
	mrc.On("MapGetKeyBytes", mock.Anything, "abc").Return(b1, nil)
	mrc.On("MapGetKeyBytes", mock.Anything, "def").Return(b2, nil)
	mrc.On("MapSetKey", mock.Anything, mock.Anything, mock.Anything).Return(nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)
	mrc.On("MapKeyDelete", mock.Anything, mock.Anything).Return(nil)

	datastore := RedisDatastore{rc: mrc}

	userManagerIDs, err := datastore.StopUsers("123", 4)

	if err != nil {
		t.Errorf("TestCreateUsersNew failed: %v", err)
	}

	assert.Equal(t, 1, len(userManagerIDs))
	mrc.AssertNumberOfCalls(t, "ListPush", 2)
	mrc.AssertNumberOfCalls(t, "MapKeyDelete", 1)
	mrc.AssertNumberOfCalls(t, "MapSetKey", 1)
}

func TestStopUsersTooMany(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	abcUsers := []string{"1", "2"}
	defUsers := []string{"3", "4", "5"}

	b1, _ := msgpack.Marshal(abcUsers)
	b2, _ := msgpack.Marshal(defUsers)

	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc", "def"}, nil)
	mrc.On("MapGetKeyBytes", mock.Anything, "abc").Return(b1, nil)
	mrc.On("MapGetKeyBytes", mock.Anything, "def").Return(b2, nil)
	mrc.On("MapSetKey", mock.Anything, mock.Anything, mock.Anything).Return(nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)
	mrc.On("MapKeyDelete", mock.Anything, mock.Anything).Return(nil)

	datastore := RedisDatastore{rc: mrc}

	userManagerIDs, err := datastore.StopUsers("123", 10)

	if err != nil {
		t.Errorf("TestCreateUsersNew failed: %v", err)
	}

	assert.Equal(t, 2, len(userManagerIDs))
}

func TestDistributeWorkEqual(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc", "def"}, nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)

	datastore := RedisDatastore{rc: mrc}

	err := datastore.DistributeWork("123", 10)

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "ListPush", 2)
	mrc.AssertCalled(t, "ListPush", "abc-work", 5)
	mrc.AssertCalled(t, "ListPush", "def-work", 5)
}

func TestDistributeWorkUnequal(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc", "def"}, nil)
	mrc.On("ListPush", mock.Anything, mock.Anything).Return(nil)

	datastore := RedisDatastore{rc: mrc}

	err := datastore.DistributeWork("123", 11)

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "ListPush", 2)
	mrc.AssertCalled(t, "ListPush", mock.Anything, 5)
	mrc.AssertCalled(t, "ListPush", mock.Anything, 6)
}

func TestGetUserWork(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	mrc.On("ListLength", mock.Anything).Return(int64(2), nil)
	mrc.On("ListPopInt", mock.Anything).Return(5, nil)

	datastore := RedisDatastore{rc: mrc}

	work, err := datastore.GetUserWork("abc")

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	assert.Equal(t, 10, work)
}

func TestMoveUserResults(t *testing.T) {
	mrc := new(mockRedisUsersClient)

	b, _ := msgpack.Marshal("foo")

	mrc.On("MapGetKeys", mock.Anything).Return([]string{"abc", "def"}, nil)
	mrc.On("ListLength", mock.Anything).Return(int64(5), nil)
	mrc.On("ListPopBytes", mock.Anything).Return(b, nil)

	datastore := RedisDatastore{rc: mrc}

	results, err := datastore.MoveUserResults("abc", 9)

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	assert.Equal(t, 9, len(results))
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
