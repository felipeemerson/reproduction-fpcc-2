import requests
import json
import os

#######################################################
#
# Process PRs: get the base commit of each PR.
# If PR_COMMIT is not first, set start_commit as the last before it
# If PR_COMMIT is first, set start_commit as pr_commit parent
# Skip PRs with PR_commit None
# Skip PRs with no pr_commit parent or len(parents) > 1
# Skip PRs with only pr_commit
#
#######################################################

query = """
query ($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      commits(first: 100) {
        edges {
          node {
            commit {
              oid
              parents(first: 2) {
                edges {
                  node {
                    oid
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

"""

TOKEN = "Bearer " + "YOUR_TOKEN"

prs_directory = "./data/raw_data"

for dirpath, dirnames, filenames in os.walk(prs_directory):
  files = [file for file in filenames if file.startswith("prs_")]

  for file in files:
    repo = file.removeprefix("prs_").removesuffix(".json")
    print(f"current repo processing: {repo}")
    
    file_path = os.path.join(dirpath, file)

    prs_file = open(file_path, "r")
    prs = json.load(prs_file)

    processed_prs = []

    for pr in prs:
      pr_commit = pr["pr_commit"]

      #if len(pr["commits"]) < 2:
      #  continue

      if pr_commit is None:
        continue

      is_pr_commit_first = pr["commits"][0]["sha"] == pr_commit

      if is_pr_commit_first:
        pr_number = pr["pr_number"]
        print(f"processing PR {pr_number}")

        url = 'https://api.github.com/graphql'
        headers = {'Authorization': TOKEN}
        variables = {
          "owner": "apache",
          "repo": repo,
          "prNumber": pr_number
        }

        response = requests.post(url, headers=headers, json={'query': query, 'variables': variables})

        if response.status_code != 200:
          print(f"Erro no PR: {pr_number}, mensagem: {response.text}")
          break

        data = response.json()
        commits = data['data']['repository']['pullRequest']["commits"]["edges"]
        start_commit = None

        for commit in commits:
          current_commit = commit["node"]["commit"]

          if current_commit["oid"] == pr_commit:
            parents = current_commit["parents"]["edges"]

            if len(parents) == 1:
              start_commit = parents[0]["node"]["oid"]

        if start_commit == None:
          continue

        print(f"PR: {pr_number}, commit base: {start_commit}")

        pr["start_commit"] = start_commit
      else:
        commits = pr["commits"]
        for index in range(len(commits)):
          if commits[index]["sha"] == pr_commit:
            start_commit = commits[index - 1]["sha"]
            pr["start_commit"] = start_commit

      pr["is_pr_commit_first"] = is_pr_commit_first

      processed_prs.append(pr)

    output_file_path = f"{prs_directory}/processed_prs_{repo}.json"

    with open(output_file_path, "w") as output:
        json.dump(processed_prs, output, indent=4)
