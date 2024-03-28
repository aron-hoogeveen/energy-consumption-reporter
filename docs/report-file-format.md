# Report File Template

This file describes the design of a JSON template that will be used for the output report files.
The template is inspired by [Tesults](https://www.tesults.com/docs/tesults-json-data-standard).

In order to design a template for effective report generation we first need to understand the needs of the users.
Once we know their needs, we also know what information we need to include.
The first constraint is that the file must be human-readable.
This will enable users to read through the test results themselves without needing any viewing tools other then a text editor.
Furthermore, we will choose a JSON file format.
This will enable developers to parse our reports and create additional tools for them.

Now we will look at what information needs to go into this JSON file.
For the basic design of the file we will use inspiration from [Tesults JSON data standard](https://www.tesults.com/docs/tesults-json-data-standard).
Resulting in the following basic template:

```json
{
	"results": {
		"name": "<user defined descriptive name>",
		<!-- other high-level information -->,
		"cases": [
			{
				"name": "<some test method name>",
				"result": "pass",
				"reason": "",
				<!-- other test-level information -->,
				"_userDefinedField": "<some value>"
			},
			{
				"name": "<another test method name>",
				"result": "fail",
				"reason": "AssertionError: Invalid Operation",
				<!-- other test-level information -->,
				"_userDefinedField": "<some value>"
			}
		]
	}
}
```

To further specify the available fields, we first identify our end users.

- us, as the designers of this energy consumption reporter tool;
- software developer teams;
- team managers.

To really comply with the users' needs, we could send out some questionairs asking the target users for their needs.
We choose to ommit this step for now and create a first version without using a questionair.

We will now go into the suspected needs for each of the identified end users.

### Software developer teams

Software developer teams work for companies.
Currently, having a low carbon footprint is hot-topic and therefore companies will want to invest time into making their software more energy efficient.
A software developer working on improving the energy consumption of a specific part of the code wants to compare the energy consumption of the original code with the new code.
They might even want to try different approaches and compare them.
Therefore, they need a way to differentiate the different reports for each of these scenarios.
All software developers (should) use a versioning system (e.g. git) to track their different versions of the code.
The energy consumption of software will differ from hardware to hardware and, therefore, the system information needs to be saved.

From these observations we extract the following high-level data fields:

- **software_version:** the current version of their software;
- **commit_hash:** a hash corresponding to a git commit;
- **date:** they want to filter on all the reports of a specific day;
- **hardware:** object containing details about the hardware the tests were executed on. This object must be extendible, since users may want to save extra information for better reproducibility.

In order to effectively compare the energy consumption of the different versions of a test, we need to save this information.
Since the end users may also need to compare the power consumption, we also need to keep track of the execution time of the tests.
For more accurate results the scenarios should be measured more than once.
Therefore, the developer can specify the number of times to execute and measure the scenario.
Furthermore, the energy measurement only makes sense for passing tests, therefore, we also need to include if a test passed or not.

We arrive at the following test-level data fields:

- **name:** name of the test function;
- **N:** the number of times the scenario/test has been run (by doing multiple runs, abnormalities can be identified);
- **energy:** list with _N_ entries corresponding to the total energy of a single execution of a scenario.
- **power:** list with _N_ entries corresponding to the average power of a single execution of a scenario.
- **execution_time:** list with _N_ entries with the execution time for each of the executions;
- **edp:** the energy delay product.
- **result:** "pass"/"fail" of the test;
- **reason:** if a test failed, the reason why it failed;

### Team managers

The team managers want to comunicate clear data/conclusions to their managers in order to show progress.
Therefore, the viewing tool must be able to display the results for specific test functions.
There are no additional data fields arrived from this requirement, but it needs to be taken into account for the creation of the viewing tool.

### The Energy Consumption Reporter team

We ourselves our also a stakeholder for this software.
We will most likely come upon new user needs when we will already have rolled out our first version.
Therefore, we must keep track of different versions of the format.
New and better estimation tools might become available to use in our reporter tool.
We must distinguish between this different models, since you cannot compare one estimation from one model with another estimation from another model.
This gives us the following additional high-level field:

- **version:** the template version number indicating the version of this report template.
- **model:** an identifier for the estimation model that was used (e.g. a link to a github repository version tag)


## The resulting JSON template

One extra thing to note is that we cannot predict all the needs of the users.
Therefore, users must be able to specify their own data fields.
User specified data fields will be prepended with an underscore "_".

The previews identified data fields resulted in the following JSON template:

```json
{
	"results": {
		"name": "Hello World!",
		"description": "This is some extra description that can be displayed for convenience.\nDo whatever you need.",
		"version": 1,
		"software_version": "v1.2BETA",
		"commit": "755f02b971d59acd85d3aa727baa0e822efcd73f",
		"date": "2024-03-11T16:50:00",
		"model": "https://github.com/green-coding-solutions/spec-power-model",
		"hardware": {
			"PC_name": "<value>",
			"CPU_name": "<value>",
			"CPU_temp": <value_in_degrees_celcius>,
			"CPU_freq": <value_in_MHz>
		},
		"cases": [
			{
				"name": "test_user_supplies_incomplete_information",
				"result": "fail",
				"reason": "AssertionError: Invalid Operation",
				"N": 3,
				"execution_time": [
					<miliseconds>,
					<miliseconds>,
					<miliseconds>
				],
				"energy": [
					<joules>,
					<joules>,
					<joules>
				],
				"power": [
					<Watts>,
					<Watts>,
					<Watts>
				],
				"edp": [
					<joules-second>,
					<joules-second>,
					<joules-second>
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
				"reason": "",
				"N": 3,
				"execution_time": [
					<miliseconds>,
					<miliseconds>,
					<miliseconds>
				],
				"energy": [
					<joules>,
					<joules>,
					<joules>
				],
				"power": [
					<Watts>,
					<Watts>,
					<Watts>
				],
				"edp": [
					<joules-second>,
					<joules-second>,
					<joules-second>
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