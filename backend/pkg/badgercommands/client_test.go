package badgercommands

import (
	"testing"
	"time"

	"github.com/dgraph-io/badger/v3"
	"github.com/stretchr/testify/assert"
)

func SetupDB(t *testing.T) *BadgerCommands {
	db, err := badger.Open(badger.DefaultOptions("").WithInMemory(true))

	if err != nil {
		t.Fatal(err)
	}

	return NewBadgerCommands(db)
}

func TestListLength(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.ListPush("my-list", 1)
	commands.ListPush("my-list", true)
	commands.ListPush("my-list", "a")

	length, err := commands.ListLength("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, int64(3), length)
}

func TestListLengthEmpty(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	length, err := commands.ListLength("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, int64(0), length)
}

func TestListPopBytes(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.ListPush("my-list", []byte("foo"))

	elem, err := commands.ListPopBytes("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte("foo"), elem)

	length, err := commands.ListLength("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, int64(0), length)
}

func TestListPopBytesEmpty(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.ListPush("my-list", []byte("foo"))

	commands.ListPopBytes("my-list")
	elem, err := commands.ListPopBytes("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte(nil), elem)
}

func TestListPopBytesNotFound(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	elem, err := commands.ListPopBytes("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte(nil), elem)
}

func TestListPopInt(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.ListPush("my-list", 3)

	elem, err := commands.ListPopInt("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 3, elem)

	length, err := commands.ListLength("my-list")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, int64(0), length)
}

func TestGetBytes(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.Set("my-item", []byte("foo"), time.Hour)

	elem, err := commands.GetBytes("my-item")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte("foo"), elem)
}

func TestGetFloat(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.Set("my-item", 1.23, time.Hour)

	elem, err := commands.GetFloat("my-item")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 1.23, elem)
}

func TestGetBytesNotFound(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	elem, err := commands.GetBytes("my-item")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte(nil), elem)
}

func TestGetMin(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 4.56)
	commands.AddToSet("my-set", 1.23)
	commands.AddToSet("my-set", 7.89)

	val, err := commands.GetMin("my-set")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 1.23, val)
}

func TestGetMax(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 4.56)
	commands.AddToSet("my-set", 1.23)
	commands.AddToSet("my-set", 7.89)

	val, err := commands.GetMax("my-set", 3)

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 7.89, val)
}

func TestGetMedian(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 4.56)
	commands.AddToSet("my-set", 1.23)
	commands.AddToSet("my-set", 7.89)

	val, err := commands.GetMedian("my-set", 3)

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 4.56, val)
}

func TestGetMedianSingleElement(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 4.56)

	val, err := commands.GetMedian("my-set", 1)

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 4.56, val)
}

func TestGetMedianEven(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 1.23)
	commands.AddToSet("my-set", 4.56)
	commands.AddToSet("my-set", 7.89)
	commands.AddToSet("my-set", 10.12)

	val, err := commands.GetMedian("my-set", 2)

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 7.89, val)
}

func TestIncrementCounter(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	err := commands.IncrementCounter("my-count", 1)

	if err != nil {
		t.Fatal(t)
	}

	err = commands.IncrementCounter("my-count", 2)

	if err != nil {
		t.Fatal(t)
	}

	err = commands.IncrementCounter("my-count", 3)

	if err != nil {
		t.Fatal(t)
	}

	val, err := commands.GetFloat("my-count")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, float64(6), val)
}

func TestGetRangeCount(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.AddToSet("my-set", 1.23)
	commands.AddToSet("my-set", 4.56)
	commands.AddToSet("my-set", 7.89)
	commands.AddToSet("my-set", 10.12)

	count, err := commands.RangeCount("my-set", 0, 5)

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, int64(2), count)
}

func TestMapGet(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	err := commands.MapSetKey("my-map", "foo", []byte("abc"))

	if err != nil {
		t.Fatal(err)
	}

	val, err := commands.MapGetKeyBytes("my-map", "foo")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, []byte("abc"), val)
}

func TestMapKeys(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	err := commands.MapSetKey("my-map", "foo", []byte("abc"))

	if err != nil {
		t.Fatal(err)
	}

	err = commands.MapSetKey("my-map", "bar", []byte("def"))

	if err != nil {
		t.Fatal(err)
	}

	keys, err := commands.MapGetKeys("my-map")

	if err != nil {
		t.Fatal(err)
	}

	assert.Equal(t, 2, len(keys))
}

func TestMapDeleteKey(t *testing.T) {
	commands := SetupDB(t)

	defer commands.Close()

	commands.MapSetKey("my-map", "foo", []byte("abc"))
	commands.MapSetKey("my-map", "bar", []byte("def"))

	err := commands.MapKeyDelete("my-map", "foo")

	if err != nil {
		t.Fatal(err)
	}

	keys, _ := commands.MapGetKeys("my-map")

	assert.Equal(t, 1, len(keys))

	err = commands.MapSetKey("my-map", "baz", []byte("efg"))

	if err != nil {
		t.Fatal(err)
	}

	keys, _ = commands.MapGetKeys("my-map")

	assert.Equal(t, 2, len(keys))
}
