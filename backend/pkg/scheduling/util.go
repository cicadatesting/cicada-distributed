package scheduling

func GetTagArg(tags []string) []string {
	tagArg := []string{}

	for _, tag := range tags {
		tagArg = append(tagArg, "--tag", tag)
	}

	return tagArg
}
