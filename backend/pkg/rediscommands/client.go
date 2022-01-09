package rediscommands

import (
	"context"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

type RedisCommands struct {
	client *redis.Client
}

func NewRedisCommands(client *redis.Client) *RedisCommands {
	return &RedisCommands{client: client}
}

func (rc *RedisCommands) ListLength(key string) (int64, error) {
	return rc.client.LLen(context.Background(), key).Result()
}

func (rc *RedisCommands) ListPopBytes(key string) ([]byte, error) {
	return rc.client.LPop(context.Background(), key).Bytes()
}

func (rc *RedisCommands) ListPopInt(key string) (int, error) {
	return rc.client.LPop(context.Background(), key).Int()
}

func (rc *RedisCommands) ListPush(key string, value interface{}) error {
	return rc.client.RPush(context.Background(), key, value).Err()
}

func (rc *RedisCommands) GetBytes(key string) ([]byte, error) {
	return rc.client.Get(context.Background(), key).Bytes()
}

func (rc *RedisCommands) GetFloat(key string) (float64, error) {
	return rc.client.Get(context.Background(), key).Float64()
}

func (rc *RedisCommands) Set(key string, value interface{}, expiration time.Duration) error {
	return rc.client.Set(context.Background(), key, value, expiration).Err()
}

func (rc *RedisCommands) AddToSet(key string, score float64) error {
	item := redis.Z{
		Score:  score,
		Member: uuid.NewString(),
	}

	return rc.client.ZAdd(context.Background(), key, &item).Err()
}

func (rc *RedisCommands) GetMin(key string) (float64, error) {
	scores, err := rc.client.ZRangeWithScores(context.Background(), key, 0, 1).Result()

	if err != nil {
		return 0, err
	}

	if len(scores) < 1 {
		return 0, nil
	}

	return scores[0].Score, nil
}

func (rc *RedisCommands) GetCardinality(key string) (int64, error) {
	return rc.client.ZCard(context.Background(), key).Result()
}

func (rc *RedisCommands) GetMax(key string, setLen int64) (float64, error) {
	scores, err := rc.client.ZRangeWithScores(context.Background(), key, setLen-1, -1).Result()

	if err != nil {
		return 0, err
	}

	if len(scores) < 1 {
		return 0, nil
	}

	return scores[0].Score, nil
}

func (rc *RedisCommands) GetMedian(key string, setLen int64) (float64, error) {
	medIndex := setLen / 2

	scores, err := rc.client.ZRangeWithScores(context.Background(), key, medIndex, medIndex).Result()

	if err != nil {
		return 0, err
	}

	if len(scores) < 1 {
		return 0, nil
	}

	return scores[0].Score, nil
}

func (rc *RedisCommands) IncrementCounter(key string, amount float64) error {
	return rc.client.IncrByFloat(context.Background(), key, amount).Err()
}

func (rc *RedisCommands) RangeCount(key string, min, max float64) (int64, error) {
	minS := fmt.Sprintf("%f", min)
	maxS := fmt.Sprintf("%f", max)

	if min < 0 {
		minS = "-inf"
	}

	if max < 0 {
		maxS = "+inf"
	}

	return rc.client.ZCount(context.Background(), key, minS, maxS).Result()
}

func (rc *RedisCommands) MapSetKey(mapName, key string, value []byte) error {
	return rc.client.HSet(context.Background(), mapName, key, value).Err()
}

func (rc *RedisCommands) MapGetKeyBytes(mapName, key string) ([]byte, error) {
	return rc.client.HGet(context.Background(), mapName, key).Bytes()
}

func (rc *RedisCommands) MapGetKeys(mapName string) ([]string, error) {
	return rc.client.HKeys(context.Background(), mapName).Result()
}

func (rc *RedisCommands) MapKeyDelete(mapName string, key string) error {
	return rc.client.HDel(context.Background(), mapName, key).Err()
}
