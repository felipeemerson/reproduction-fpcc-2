import json

repos = [
    "maven-surefire",
    "accumulo",
    "commons-io",
    "directory-server",
    "lucene",
    "zookeeper",
    "mina-sshd"
]

for repo in repos:
    print("----------- Não processado -----------")
    with open(f"./data/raw_data/prs_{repo}.json") as i:
        print(f"REPO: {repo} - {len(json.load(i))}")

    print("----------- Processado -----------")
    with open(f"./data/raw_data/processed_prs_{repo}.json") as i:
        prs = json.load(i)
        print(f"REPO: {repo} - {len(prs)}")

        filtered = 0

        for pr in prs:
            is_pr_commit_first = pr["is_pr_commit_first"]

            commits = pr["commits"]
        

            if is_pr_commit_first:
                commits.insert(0, pr["start_commit"])
            else:
                start_commit_index = [i for i, commit in enumerate(commits) if commit["sha"] == pr["start_commit"]][0]
                commits = commits[start_commit_index:]

            if len(commits) > 2:
                filtered += 1

        print("----------- Com commit after pr_commit -----------")
        print(f"REPO: {repo} - {filtered}")
