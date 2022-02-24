package types

const NotFound = NotFoundError("Not Found")

type NotFoundError string

func (e NotFoundError) Error() string { return string(e) }
