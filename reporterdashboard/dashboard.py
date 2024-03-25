import json


def get_matching_test_cases(test_cases_1, test_cases_2):
    # copy the lists over to a new object
    sorted_1 = sorted(test_cases_1, key=lambda d: d["name"])
    sorted_2 = sorted(test_cases_2, key=lambda d: d["name"])
    overlapping_test_cases = []

    while True:
        if len(sorted_1) == 0 or len(sorted_2) == 0:
            break

        if sorted_1[0]["name"] == sorted_2[0]["name"]:
            overlapping_test_cases.append((sorted_1.pop(0), sorted_2.pop(0)))
        elif sorted_1[0]["name"] < sorted_2[0]["name"]:
            sorted_1.pop(0)
        else:
            sorted_2.pop(0)
    return overlapping_test_cases


if __name__ == "__main__":
    # read the two file paths from arguments
    file1_path = "example-reports/report1.json"
    file2_path = "example-reports/report2.json"
    with open(file1_path) as f:
        file1_data = json.load(f)
    with open(file2_path) as f:
        file2_data = json.load(f)

    # TODO make sure both tests were run on the same hardware

    file1_data = file1_data["results"]["cases"]
    file2_data = file2_data["results"]["cases"]

    matching_test_cases = get_matching_test_cases(file1_data, file2_data)

    print(matching_test_cases)

