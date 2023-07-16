import json
import os

#######################################################
#
# Filter PRs: exclude PRs with no commit after pr_commit
#
#######################################################

prs_directory = './data/raw_data/'

for dirpath, dirnames, filenames in os.walk(prs_directory):
    for file in filenames:
        if not file.startswith("processed_prs_"):
            continue

        file_path = os.path.join(dirpath, file)

        with open(file_path, "r") as input_file:
            prs = json.load(input_file)
            filtered_prs = []

            for pr in prs:
                is_pr_commit_first = pr["is_pr_commit_first"]

                commits = pr["commits"].copy()

                if is_pr_commit_first:
                    commits.insert(0, pr["start_commit"])
                else:
                    start_commit_index = [i for i, commit in enumerate(commits) if commit["sha"] == pr["start_commit"]][0]
                    commits = commits[start_commit_index:]

                if len(commits) > 2:
                    filtered_prs.append(pr)

            output_path = file.removeprefix("processed_prs_")
            output_path = prs_directory + "filtered_prs_" + output_path

            with open(output_path, "w") as output:
                print(f"len filtered prs: {len(filtered_prs)}")
                json.dump(filtered_prs, output, indent=4)
