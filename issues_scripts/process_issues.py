import json
import os
import re

def process_issues(issues):
    init_raw_issues = issues[0]["issues"]["issues"]

    past_issues = set([issue["key"] for issue in init_raw_issues])
    not_resolved_inside_issues = set()
    resolved_past_issues = set()
    resolved_inside_issues = set()
    not_resolved_past_issues = set()
    OPEN = "OPEN"
    CLOSED = "CLOSED"

    last_issues = issues[-1]["issues"]["issues"]

    for issue in last_issues:
        issue_key = issue["key"]
        issue_status = issue["status"]

        if issue_key not in past_issues and issue_status == OPEN:
            not_resolved_inside_issues.add(issue_key)
        elif issue_key not in past_issues and issue_status == CLOSED:
            resolved_inside_issues.add(issue_key)
        elif issue_key in past_issues and issue_status == OPEN:
            not_resolved_past_issues.add(issue_key)
        elif issue_key in past_issues and issue_status == CLOSED:
           resolved_past_issues.add(issue_key)

    total_resolved = len(resolved_past_issues) + len(resolved_inside_issues)
    total_not_resolved = len(not_resolved_past_issues) + len(not_resolved_inside_issues)
    total = total_resolved + total_not_resolved

    processed_issues = {
       "resolved_past": len(resolved_past_issues),
       "resolved_inside": len(resolved_inside_issues),
       "not_resolved_past": len(not_resolved_past_issues),
       "not_resolved_inside": len(not_resolved_inside_issues),
       "total_resolved": total_resolved,
       "total_not_resolved": total_not_resolved,
       "total": total
    }

    return processed_issues
  
issues_directory = "./data/issues"
processed_data_file_path = "./data/processed_data/processed_issues.json"

processed_issues = []

for dirpath, dirnames, filenames in os.walk(issues_directory):

  for file in filenames:
    current_issues_file = open(f"{issues_directory}/{file}", "r")

    current_issues = json.load(current_issues_file)

    current_processed_issues = process_issues(current_issues)

    match = re.match(r'issues_(.*)_(\d+).json', file)

    current_processed_issues["repo"] = match.group(1)
    current_processed_issues["pr_number"] = int(match.group(2))

    processed_issues.append(current_processed_issues)

with open(processed_data_file_path, "w") as output:
   json.dump(processed_issues, output, indent=4)