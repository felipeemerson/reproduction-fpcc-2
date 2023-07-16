import json

prs_directory = "./data/raw_data"
processed_data_directory = "./data/processed_data"

repos = [
    "accumulo",
    "commons-io",
    "maven-surefire"
]

prepared_normal_prs = []
prepared_filtered_prs = []

for repo in repos:
    with open(f"{prs_directory}/filtered_prs_{repo}.json", "r") as input_file:
        prs = json.load(input_file)

        for pr in prs:
            prepared_pr = {}
            prepared_pr["qnt_commits"] = len(pr["commits"])
            prepared_pr["pr_number"] = pr["pr_number"]
            prepared_pr["repo"] = repo
            prepared_pr["is_pr_commit_first"] = pr["is_pr_commit_first"]

            prepared_filtered_prs.append(prepared_pr)
    
    with open(f"{prs_directory}/prs_{repo}.json", "r") as input_file:
        prs = json.load(input_file)

        for pr in prs:
            prepared_pr = {}
            prepared_pr["qnt_commits"] = len(pr["commits"])
            prepared_pr["pr_number"] = pr["pr_number"]
            prepared_pr["repo"] = repo

            prepared_normal_prs.append(prepared_pr)

with open(f"{processed_data_directory}/processed_prs.json", "w") as output:
    json.dump(prepared_normal_prs, output)

with open(f"{processed_data_directory}/processed_filtered_prs.json", "w") as output:
    json.dump(prepared_filtered_prs, output)