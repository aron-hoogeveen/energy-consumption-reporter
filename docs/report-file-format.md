# Report File Format

This file describes the design of a JSON format that will be used as report file.
The format is inspired by [Tesults](https://www.tesults.com/docs/tesults-json-data-standard).

**TODO:** for each field, add a reason why it is essential that it should be included.

```json
{
	"results": {
		"name": "Hello World!",
		"description": "This is some extra description that can be displayed for convenience.\nDo whatever you need.",
		"version": "v1", <!-- is a version number needed? It could be nice for future breaking changes -->
		"software_version": "v1.2BETA", <!-- the version of the software/system under test -->
		"commit": "755f02b971d59acd85d3aa727baa0e822efcd73f", <!-- possibly a commit hash from a git repo for comparing software with the same version but actual different code -->
		"date": "2024-03-11T16:50:00",
		"model": "https://github.com/green-coding-solutions/spec-power-model", <!-- the plugin must allow to use different estimation techniques/models. We should save the configuration -->
		"cases": [
			{
				"name": "test_user_supplies_incomplete_information",
				"result": "fail",
				"reason": "AssertionError: Invalid Operation",
				"duration": "<milliseconds>",
				"interval": "<milliseconds>", <!-- interval between estimating energy consumption -->
				"energy_avg": "<joules>", <!-- we should not include both energy and power, because of rounding errors (or make sure that there won't be any rounding errors). Result should be consistent.
				"N": "<number_of_executions>", <!-- how many times the test method was executed.
				"energy": [
					"<joules>",
					"<joules>",
					...,
					"<joules>"
				],
				"_my_custom_field": "This is so epic!",
				"_test_params": {
					"param1": "<value1>",
					"param2": "<value2>"
				}
			},
			{
				"name": "test_user_supplies_complete_information",
				"result": "pass",
				"reason": "", <!-- should we ommit this, since the result was "pass?" or should we always include this?
				"duration": "<milliseconds>",
				"interval": "<milliseconds>", <!-- interval between estimating energy consumption -->
				"energy_avg": "<joules>",
				"N": "<number_of_executions>", <!-- how many times the test method was executed.
				"energy": [
					"<joules>",
					"<joules>",
					...,
					"<joules>"
				],
				"_my_custom_field": "This is so epic!",
				"_test_params": {
					"param1": "<value1>",
					"param2": "<value2>"
				}
			}
		]
	}
}
```