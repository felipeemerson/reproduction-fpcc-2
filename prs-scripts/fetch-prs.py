import requests
import json
from datetime import datetime
import pytz

query = """
query (
  $owner_query: String = "apache"
  $repo_query: String = "maven-surefire"
  $after_var: String
) {
  repository(owner: $owner_query, name: $repo_query) {
    pullRequests(
      first: 100
      after: $after_var
      orderBy: { field: CREATED_AT, direction: DESC }
      states: MERGED
    ) {
      totalCount
      edges {
        node {
          number
          createdAt
          commits(first: 100) {
            totalCount
            nodes {
              commit {
                oid
                committer {
                  date
                }
              }
            }
          }
          timelineItems(last: 10, itemTypes: [HEAD_REF_FORCE_PUSHED_EVENT]) {
            totalCount
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

token = "Bearer " + "YOUR_TOKEN"

def process_pull_request(pr):
    pr_timeline_items_count = pr['node']['timelineItems']['totalCount']

    if pr_timeline_items_count > 0:
        return None

    pr_number = pr['node']['number']
    pr_created_at = pr['node']['createdAt']
    if pr_created_at.endswith("Z"):
        pr_created_at = pr_created_at[:-1]  # Remover 'Z'
    pr_created_at = datetime.fromisoformat(pr_created_at)
    pr_created_at = pr_created_at.replace(tzinfo=pytz.utc)

    pr_commits = pr['node']['commits']['nodes']
    pr_commits_processed = []
    pr_commit = None

    for commit in pr_commits:
        commit_sha = commit['commit']['oid']
        commit_created_at = commit['commit']['committer']['date']
        commit_created_at = datetime.strptime(
            commit_created_at, "%Y-%m-%dT%H:%M:%S%z")

        if commit_created_at < pr_created_at:
            pr_commit = commit_sha

        pr_commits_processed.append({
            'sha': commit_sha,
            'created_at': str(commit_created_at)
        })

    return {
        'pr_number': pr_number,
        'created_at': str(pr_created_at),
        'commits': pr_commits_processed,
        'pr_commit': pr_commit
    }


def fetch_pull_requests(owner, repo):
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': token}
    has_next_page = True
    after = None
    pull_requests = []

    while has_next_page:
        variables = {
            'owner_query': owner,
            'repo_query': repo,
            'after_var': after
        }
        response = requests.post(url, headers=headers, json={
                                 'query': query, 'variables': variables})
        data = response.json()

        for edge in data['data']['repository']['pullRequests']['edges']:
            pr = process_pull_request(edge)
            if pr:
                pull_requests.append(pr)

        page_info = data['data']['repository']['pullRequests']['pageInfo']
        has_next_page = page_info['hasNextPage']
        after = page_info['endCursor']

    return pull_requests


owner = 'apache'
repos = ["maven-surefire", "commons-io", "accumulo",
         "mina-sshd", "zookeeper", "lucene", "directory-server"]


for repo in repos:
    pull_requests = fetch_pull_requests(owner, repo)

    with open(f"./data/raw_data/prs_{repo}.json", "w") as output_file:
        json.dump(pull_requests, output_file, indent=4)