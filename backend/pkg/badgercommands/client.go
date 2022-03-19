package badgercommands

import (
	"fmt"
	"reflect"
	"sync"
	"time"

	"github.com/cicadatesting/backend/pkg/types"
	"github.com/dgraph-io/badger/v3"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
	"github.com/vmihailenco/msgpack/v5"
	"github.com/wangjia184/sortedset"
)

type BadgerCommands struct {
	db             *badger.DB
	setMapLock     sync.Mutex
	counterMapLock sync.Mutex
	sets           map[string]*sortedset.SortedSet
	counters       map[string]float64
}

func NewBadgerCommands(db *badger.DB) *BadgerCommands {
	return &BadgerCommands{
		db:       db,
		sets:     map[string]*sortedset.SortedSet{},
		counters: map[string]float64{},
	}
}

func (bc *BadgerCommands) Close() error {
	return bc.db.Close()
}

func (bc *BadgerCommands) ListLength(key string) (int64, error) {
	length := int64(0)

	err := bc.db.View(func(txn *badger.Txn) error {
		// get list by key
		listItem, err := txn.Get([]byte(key))

		if err == badger.ErrKeyNotFound {
			return nil
		}

		if err != nil {
			return fmt.Errorf("Error getting list: %v", err)
		}

		// copy list length
		listItem.Value(func(val []byte) error {
			list := []interface{}{}

			err := msgpack.Unmarshal(val, &list)

			if err != nil {
				return fmt.Errorf("Error loading list: %v", err)
			}

			length = int64(len(list))

			return nil
		})

		return nil
	})

	return length, err
}

func (bc *BadgerCommands) ListPush(key string, value interface{}) error {
	var err error

	for {
		err = bc.db.Update(func(txn *badger.Txn) error {
			// get list by key
			listItem, err := txn.Get([]byte(key))

			if err != nil && err != badger.ErrKeyNotFound {
				return fmt.Errorf("Error getting list: %v", err)
			}

			list := []interface{}{}

			// if list not exist, create new list with single element
			// else, push into list
			if err == badger.ErrKeyNotFound {
				list = append(list, value)
			} else {
				listItemBytes, err := listItem.ValueCopy(nil)

				if err != nil {
					return fmt.Errorf("Error getting list value: %v", err)
				}

				err = msgpack.Unmarshal(listItemBytes, &list)

				if err != nil {
					return fmt.Errorf("Error loading list: %v", err)
				}

				list = append(list, value)
			}

			// save list
			newListBytes, err := msgpack.Marshal(list)

			if err != nil {
				return fmt.Errorf("Error serializing new list: %v", err)
			}

			err = txn.Set([]byte(key), newListBytes)

			if err != nil {
				return fmt.Errorf("Error saving list: %v", err)
			}

			return nil
		})

		if err == nil || err != badger.ErrConflict {
			break
		}

		err = nil
		logrus.Warn("Transaction conflict pushing list, retrying...")
	}

	return err
}

func (bc *BadgerCommands) ListPop(key string) (interface{}, error) {
	var elem interface{}
	var err error

	// get list
	for {
		err = bc.db.Update(func(txn *badger.Txn) error {
			// get list by key
			listItem, err := txn.Get([]byte(key))

			if err == badger.ErrKeyNotFound {
				elem = nil
				return nil
			}

			if err != nil {
				return fmt.Errorf("Error getting list: %v", err)
			}

			list := []interface{}{}

			listItemBytes, err := listItem.ValueCopy(nil)

			if err != nil {
				return fmt.Errorf("Error getting list value: %v", err)
			}

			err = msgpack.Unmarshal(listItemBytes, &list)

			if err != nil {
				return fmt.Errorf("Error loading list: %v", err)
			}

			if len(list) == 0 {
				elem = nil
				return nil
			} else {
				elem = list[0]

				if len(list) == 1 {
					list = []interface{}{}
				} else {
					list = list[1:]
				}
			}

			// save list
			newListBytes, err := msgpack.Marshal(list)

			if err != nil {
				return fmt.Errorf("Error serializing new list: %v", err)
			}

			err = txn.Set([]byte(key), newListBytes)

			if err != nil {
				return fmt.Errorf("Error saving list: %v", err)
			}

			return nil
		})

		if err == nil || err != badger.ErrConflict {
			break
		}

		err = nil
		logrus.Warn("Transaction conflict popping list, retrying...")
	}

	return elem, err
}

func (bc *BadgerCommands) ListPopBytes(key string) ([]byte, error) {
	elem, err := bc.ListPop(key)

	if err != nil {
		return nil, err
	}

	if elem == nil {
		return nil, nil
	}

	elemBytes, ok := elem.([]byte)

	if !ok {
		return nil, fmt.Errorf("List item not castable to bytes")
	}

	return elemBytes, nil
}

func (bc *BadgerCommands) ListPopInt(key string) (int, error) {
	elem, err := bc.ListPop(key)

	if err != nil {
		return 0, err
	}

	if elem == nil {
		return 0, nil
	}

	switch elem := elem.(type) {
	case int, int8, int16, int32, int64:
		return int(reflect.ValueOf(elem).Int()), nil
	}

	return 0, fmt.Errorf("List item not castable to int")
}

func (bc *BadgerCommands) GetItem(key string) (interface{}, error) {
	var elem interface{}

	err := bc.db.View(func(txn *badger.Txn) error {
		// get list by key
		item, err := txn.Get([]byte(key))

		if err == badger.ErrKeyNotFound {
			return nil
		}

		if err != nil {
			return fmt.Errorf("Error getting item: %v", err)
		}

		itemBytes, err := item.ValueCopy(nil)

		if err != nil {
			return fmt.Errorf("Error getting value: %v", err)
		}

		err = msgpack.Unmarshal(itemBytes, &elem)

		if err != nil {
			return fmt.Errorf("Error loading item: %v", err)
		}

		return nil
	})

	return elem, err
}

func (bc *BadgerCommands) GetBytes(key string) ([]byte, error) {
	elem, err := bc.GetItem(key)

	if err != nil {
		return nil, err
	}

	if elem == nil {
		return nil, types.NotFound
	}

	elemBytes, ok := elem.([]byte)

	if !ok {
		return nil, fmt.Errorf("List item not castable to bytes")
	}

	return elemBytes, nil
}

func (bc *BadgerCommands) GetFloat(key string) (float64, error) {
	elem, err := bc.GetItem(key)

	if err != nil {
		return 0, err
	}

	if elem == nil {
		return 0, types.NotFound
	}

	elemFloat, ok := elem.(float64)

	if !ok {
		return 0, fmt.Errorf("List item not castable to bytes")
	}

	return elemFloat, nil
}

func (bc *BadgerCommands) Set(key string, value interface{}, expiration time.Duration) error {
	return bc.db.Update(func(txn *badger.Txn) error {
		valueBytes, err := msgpack.Marshal(value)

		if err != nil {
			return fmt.Errorf("Error encoding value: %v", err)
		}

		e := badger.NewEntry([]byte(key), valueBytes).WithTTL(expiration)

		err = txn.SetEntry(e)

		if err != nil {
			return fmt.Errorf("Error setting key: %v", err)
		}

		return nil
	})
}

func (bc *BadgerCommands) AddToSet(key string, score float64) error {
	bc.setMapLock.Lock()
	defer bc.setMapLock.Unlock()

	set, hasSet := bc.sets[key]

	if !hasSet {
		set = sortedset.New()
	}

	set.AddOrUpdate(uuid.NewString(), sortedset.SCORE(score*10_000), score)
	bc.sets[key] = set

	return nil
}

func (bc *BadgerCommands) GetMin(key string) (float64, error) {
	set, hasSet := bc.sets[key]

	if !hasSet {
		return 0, types.NotFound
	}

	min := set.PeekMin()

	if min == nil {
		return 0, nil
	}

	return min.Value.(float64), nil
}

func (bc *BadgerCommands) GetCardinality(key string) (int64, error) {
	set, hasSet := bc.sets[key]

	if !hasSet {
		return 0, nil
	}

	return int64(set.GetCount()), nil
}

func (bc *BadgerCommands) GetMax(key string, setLen int64) (float64, error) {
	// NOTE: should maybe change redis commands to not need set length
	set, hasSet := bc.sets[key]

	if !hasSet {
		return 0, nil
	}

	max := set.PeekMax()

	if max == nil {
		return 0, nil
	}

	return max.Value.(float64), nil
}

func (bc *BadgerCommands) GetMedian(key string, setLen int64) (float64, error) {
	set, hasSet := bc.sets[key]

	if !hasSet {
		return 0, nil
	}

	medIndex := set.GetCount() / 2

	medianScores := set.GetByRankRange(medIndex+1, medIndex+1, false)

	if len(medianScores) < 1 {
		return 0, nil
	}

	return medianScores[0].Value.(float64), nil
}

func (bc *BadgerCommands) IncrementCounter(key string, amount float64) error {
	return bc.db.Update(func(txn *badger.Txn) error {
		currentValue, err := txn.Get([]byte(key))

		if err != nil && err != badger.ErrKeyNotFound {
			return fmt.Errorf("Error getting current value")
		}

		total := amount

		if err == nil {
			var currentTotal float64
			currentValueBytes, err := currentValue.ValueCopy(nil)

			if err != nil {
				return fmt.Errorf("Error loading current value: %v", err)
			}

			err = msgpack.Unmarshal(currentValueBytes, &currentTotal)

			if err != nil {
				return fmt.Errorf("Error getting current total: %v", err)
			}

			total += currentTotal
		}

		valueBytes, err := msgpack.Marshal(total)

		if err != nil {
			return fmt.Errorf("Error encoding value: %v", err)
		}

		e := badger.NewEntry([]byte(key), valueBytes)

		err = txn.SetEntry(e)

		if err != nil {
			return fmt.Errorf("Error setting key: %v", err)
		}

		return nil
	})
}

func (bc *BadgerCommands) RangeCount(key string, min, max float64) (int64, error) {
	set, hasSet := bc.sets[key]

	if !hasSet {
		return 0, types.NotFound
	}

	scores := set.GetByScoreRange(sortedset.SCORE(min*10_000), sortedset.SCORE(max*10_000), nil)

	return int64(len(scores)), nil
}

func (bc *BadgerCommands) MapSetKey(mapName, key string, value []byte) error {
	return bc.db.Update(func(txn *badger.Txn) error {
		// get map by key
		mapItem, err := txn.Get([]byte(mapName))

		if err != nil && err != badger.ErrKeyNotFound {
			return fmt.Errorf("Error getting map: %v", err)
		}

		byteMap := map[string][]byte{}

		if err == nil {
			mapItemBytes, err := mapItem.ValueCopy(nil)

			if err != nil {
				return fmt.Errorf("Error getting map value: %v", err)
			}

			err = msgpack.Unmarshal(mapItemBytes, &byteMap)

			if err != nil {
				return fmt.Errorf("Error loading map: %v", err)
			}
		}

		byteMap[key] = value

		// save map
		newMapBytes, err := msgpack.Marshal(byteMap)

		if err != nil {
			return fmt.Errorf("Error serializing new map: %v", err)
		}

		err = txn.Set([]byte(mapName), newMapBytes)

		if err != nil {
			return fmt.Errorf("Error saving map: %v", err)
		}

		return nil
	})
}

func (bc *BadgerCommands) MapGetKeyBytes(mapName, key string) ([]byte, error) {
	item, err := bc.GetItem(mapName)

	if err != nil {
		return nil, err
	}

	if item == nil {
		return nil, nil
	}

	itemMap, ok := item.(map[string]interface{})

	if !ok {
		return nil, fmt.Errorf("Item not castable to map")
	}

	val, ok := itemMap[key]

	if !ok {
		return nil, nil
	}

	valBytes, ok := val.([]byte)

	if !ok {
		return nil, fmt.Errorf("Value not castable to bytes")
	}

	return valBytes, nil
}

func (bc *BadgerCommands) MapGetKeys(mapName string) ([]string, error) {
	item, err := bc.GetItem(mapName)

	if err != nil {
		return nil, err
	}

	if item == nil {
		return nil, nil
	}

	itemMap, ok := item.(map[string]interface{})

	if !ok {
		return nil, fmt.Errorf("Item not castable to map")
	}

	keys := []string{}

	for key := range itemMap {
		keys = append(keys, key)
	}

	return keys, nil
}

func (bc *BadgerCommands) MapKeyDelete(mapName string, key string) error {
	return bc.db.Update(func(txn *badger.Txn) error {
		// get map by key
		mapItem, err := txn.Get([]byte(mapName))

		if err != nil && err != badger.ErrKeyNotFound {
			return fmt.Errorf("Error getting map: %v", err)
		}

		if err == badger.ErrKeyNotFound {
			return nil
		}

		byteMap := map[string][]byte{}

		mapItemBytes, err := mapItem.ValueCopy(nil)

		if err != nil {
			return fmt.Errorf("Error getting map value: %v", err)
		}

		err = msgpack.Unmarshal(mapItemBytes, &byteMap)

		if err != nil {
			return fmt.Errorf("Error loading map: %v", err)
		}

		// delete key if exists
		_, hasKey := byteMap[key]

		if !hasKey {
			return nil
		}

		delete(byteMap, key)

		// save map
		newMapBytes, err := msgpack.Marshal(byteMap)

		if err != nil {
			return fmt.Errorf("Error serializing new map: %v", err)
		}

		err = txn.Set([]byte(mapName), newMapBytes)

		if err != nil {
			return fmt.Errorf("Error saving map: %v", err)
		}

		return nil
	})
}
