package pkg

import (
	"context"
	"testing"

	"github.com/go-redis/redis/v8"
	"github.com/stretchr/testify/mock"
)

type mockRedisClient struct {
	redis.Client
	mock.Mock
}

func (mrc *mockRedisClient) RPush(ctx context.Context, key string, values ...interface{}) *redis.IntCmd {
	mrc.Called(ctx, key, values)
	return &redis.IntCmd{}
}

func TestDistributeWorkEqual(t *testing.T) {
	mrc := new(mockRedisClient)

	mrc.On("RPush", mock.Anything, mock.Anything, mock.Anything).Return(nil)

	datastore := Datastore{Rds: mrc}

	err := datastore.DistributeWork(context.Background(), 10, []string{"abc", "def"})

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "RPush", 2)
	mrc.AssertCalled(t, "RPush", mock.Anything, "abc-work", []interface{}{5})
	mrc.AssertCalled(t, "RPush", mock.Anything, "def-work", []interface{}{5})
}

func TestDistributeWorkUnequal(t *testing.T) {
	mrc := new(mockRedisClient)

	mrc.On("RPush", mock.Anything, mock.Anything, mock.Anything).Return(nil)

	datastore := Datastore{Rds: mrc}

	err := datastore.DistributeWork(context.Background(), 11, []string{"abc", "def"})

	if err != nil {
		t.Errorf("TestDistributeWorkEqual failed: %v", err)
	}

	mrc.AssertNumberOfCalls(t, "RPush", 2)
	mrc.AssertCalled(t, "RPush", mock.Anything, mock.Anything, []interface{}{5})
	mrc.AssertCalled(t, "RPush", mock.Anything, mock.Anything, []interface{}{6})
}
