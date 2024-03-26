import json
import argparse


def get_matching_test_cases(test_cases_1, test_cases_2):
    """Returns test cases that are both in test_cases_1 and test_cases_2.

    Test cases are ordered by their name.
    """
    # create sorted copies
    sorted_1 = sorted(test_cases_1, key=lambda d: d["name"])
    sorted_2 = sorted(test_cases_2, key=lambda d: d["name"])
    overlapping_test_cases = []

    while True:
        if len(sorted_1) == 0 or len(sorted_2) == 0:
            break

        if sorted_1[0]["name"] == sorted_2[0]["name"]:
            # only include passing tests
            if sorted_1[0]["result"] != "pass" or sorted_2[0]["result"] != "pass":
                sorted_1.pop(0)
                sorted_2.pop(0)
                continue
            overlapping_test_cases.append((sorted_1.pop(0), sorted_2.pop(0)))
        elif sorted_1[0]["name"] < sorted_2[0]["name"]:
            sorted_1.pop(0)
        else:
            sorted_2.pop(0)
    return overlapping_test_cases


def print_energy_differences(data):
    """Prints the energy difference for every test combination tuple in data.

    Keyword arguments:
    data -- list of tuples each containing two test measurements
    """
    for testcombi in data:
        # calculate average information
        if len(testcombi) != 2:
            raise TypeError(
                f"Data tuple should have two data objects (actual is {len(testcombi)})."
            )
        N_0 = testcombi[0]["N"]
        e_0 = 0
        p_0 = 0
        t_0 = 0
        for i in range(0, N_0):
            e_0 += testcombi[0]["energy"][i]
            p_0 += testcombi[0]["power"][i]
            t_0 += testcombi[0]["execution_time"][i]
        e_0 /= N_0
        p_0 /= N_0
        t_0 /= N_0

        N_1 = testcombi[1]["N"]
        e_1 = 0
        p_1 = 0
        t_1 = 0
        for i in range(0, N_1):
            e_1 += testcombi[1]["energy"][i]
            p_1 += testcombi[1]["power"][i]
            t_1 += testcombi[1]["execution_time"][i]
        e_1 /= N_1
        p_1 /= N_1
        t_1 /= N_1

        print(
            f"Test: {testcombi[0]['name']}\n"
            f"  Run 1:\n"
            f"    Time: {t_0} [ms]\n"
            f"    Energy: {e_0} [J]\n"
            f"    Power: {p_0} [W]\n"
            f"  Run 2:\n"
            f"    Time: {t_1} [ms]\n"
            f"    Energy: {e_1} [J]\n"
            f"    Power: {p_1} [W]\n"
            f"  Difference (run 2 - run 1):\n"
            f"    Time: {t_1 - t_0} [ms]\n"
            f"    Energy: {e_1 - e_0} [J]\n"
            f"    Power: {p_1 - p_0} [W]\n"
            f"\n"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ReporterDashboard",
        description="Displays energy differences between two reports.",
    )
    parser.add_argument("report1", help="full path to the first report")
    parser.add_argument("report2", help="full path to the second report")

    return parser


if __name__ == "__main__":
    parser = _parser()
    args = parser.parse_args()

    with open(args.report1) as f:
        file1_data = json.load(f)
    with open(args.report2) as f:
        file2_data = json.load(f)

    file1_data = file1_data["results"]["cases"]
    file2_data = file2_data["results"]["cases"]

    matching_test_cases = get_matching_test_cases(file1_data, file2_data)

    print_energy_differences(matching_test_cases)
