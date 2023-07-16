import requests
import json
import zipfile
import io
import shutil
import subprocess
import time
import os
import traceback
import logging
import re

logging.basicConfig(filename='./data/logs/log.txt', level=logging.ERROR)

current_repo = "accumulo"

def create_sonar_project(pr_number):
    global current_repo

    if get_project(pr_number) == 200:
        print("Sonar project already exists")
        return

    endpoint = f"{SONAR_API_URL}/projects/create"

    querystring = {
        "name": f"{current_repo}-{pr_number}",
        "project": f"{current_repo}-{pr_number}",
    }

    requests.post(endpoint, params=querystring, auth=(USERNAME, PASSWORD))


def get_project(pr_number):
    global current_repo
    endpoint = f"{SONAR_API_URL}/components/show"

    querystring = {"component": f"{current_repo}-{pr_number}"}

    response = requests.get(endpoint, params=querystring,
                            auth=(USERNAME, PASSWORD))

    return response.status_code


def create_sonar_token(pr_number):
    global current_repo
    print(f"Creating sonar token for PR: {pr_number}")
    create_sonar_project(pr_number)

    endpoint = f"{SONAR_API_URL}/user_tokens/generate"

    querystring = {
        "name": f"{current_repo}-{pr_number}",
        "projectKey": f"{current_repo}-{pr_number}",
        "type": "PROJECT_ANALYSIS_TOKEN",
    }

    response = requests.post(
        endpoint, params=querystring, auth=(USERNAME, PASSWORD))

    json = response.json()

    print(json)

    return json["token"]


def get_sonar_issues(pr_number):
    global current_repo
    endpoint = f"{SONAR_API_URL}/issues/search"

    page = 1
    page_size = 500

    issues = {
        "issues": [],
        "total": 0
    }

    # sleep 60s to data can be loaded
    time.sleep(60)

    while True:
        querystring = {
            "componentKeys": f"{current_repo}-{pr_number}",
            "languages": "java",
            "p": page,
            "ps": page_size,
        }

        response = requests.get(endpoint, params=querystring)
        if response.status_code != 200:
            raise Exception("Failed to get issues")
        response = response.json()

        for issue in response["issues"]:
            filtered_issue = {}

            for field in ISSUE_FIELDS:
                filtered_issue[field] = issue[field]

            issues["issues"].append(filtered_issue)

        total_issues = response["total"]
        current_number_issues = page * page_size

        print(f"response {response}")

        print(f"total issues {total_issues}")
        print(f"current number issues {current_number_issues}")

        page += 1

        if current_number_issues >= total_issues or page == 21:
            issues["total"] = total_issues
            break

    return issues


def delete_sonar_project(pr_number):
    global current_repo

    endpoint = f"{SONAR_API_URL}/projects/delete"

    querystring = {
        "project": f"{current_repo}-{pr_number}"
    }

    requests.post(endpoint, params=querystring, auth=(USERNAME, PASSWORD))


def download_commit(project_url, commit_sha):
    commit_url = f"{project_url}/archive/{commit_sha}.zip"

    response = requests.get(commit_url, stream=True)

    zip = zipfile.ZipFile(io.BytesIO(response.content))
    zip.extractall()

def check_prs_to_process(prs):
    global current_repo
    all_prs = {}

    for pr in prs:
        all_prs[pr["pr_number"]] = pr

    issues_directory = "./data/issues"

    for _, _, filenames in os.walk(issues_directory):
        current_processed_prs =  set([int(file.removeprefix(f"issues_{current_repo}_").removesuffix(".json")) for file in filenames if current_repo in file])

    with open(f"./data/logs/exclude_prs_{current_repo}.json", "r") as input:
        excluded_prs = json.load(input)
    
    prs_to_process = [all_prs[pr_number] for pr_number in all_prs.keys() if pr_number not in current_processed_prs and str(pr_number) not in excluded_prs.keys()]

    return prs_to_process

def create_exclude_prs_file():
    global current_repo

    exclude_file_path = f"./data/logs/exclude_prs_{current_repo}.json"

    if (os.path.exists(exclude_file_path)):
        return
    
    with open(exclude_file_path, "w") as output:
        json.dump({}, output)

def add_pr_to_exclude_prs(pr_number, reason):
    global current_repo

    exclude_file_path = f"./data/logs/exclude_prs_{current_repo}.json"

    exclude_file = open(exclude_file_path, "r")
    excluded_prs = json.load(exclude_file)
    exclude_file.close()

    excluded_prs[pr_number] = reason

    with open(exclude_file_path, "w") as output:
        json.dump(excluded_prs, output, indent=4)

def check_build_files(commit_sha):
    global current_repo

    pom_location = f"./{current_repo}-{commit_sha}/pom.xml"
    build_gradle_location = f"./{current_repo}-{commit_sha}/build.gradle"
    gradlew_location = f"./{current_repo}-{commit_sha}/gradlew"

    if "mvn" in COMMAND_TO_COMPILE and not os.path.exists(pom_location):
        shutil.rmtree(f"{current_repo}-{commit_sha}")
        error_msg = f"Pom file not found, skiping PR: {current_pr}"
        add_pr_to_exclude_prs(current_pr, error_msg)
        raise Exception(error_msg)
    elif "gradlew" in COMMAND_TO_COMPILE:
        if not os.path.exists(build_gradle_location) or not os.path.exists(gradlew_location):
            shutil.rmtree(f"{current_repo}-{commit_sha}")
            error_msg = f"Gradle file(s) missing, skiping PR: {current_pr}"
            add_pr_to_exclude_prs(current_pr, error_msg)
            raise Exception(error_msg)
        
        add_sonar_plugin_gradle(build_gradle_location)

def add_sonar_plugin_gradle(build_gradle_location):
    global current_repo

    build_gradle_file = open(build_gradle_location, "r")
    build_gradle_contents = build_gradle_file.read()

    # Encontre o bloco de plugins
    plugins_block = re.search(r"plugins\s*\{(.*?)\}", build_gradle_contents, re.DOTALL)
    print(plugins_block.group(1))

    # Adicione a linha do plugin SonarQube ao bloco
    if plugins_block:
        plugins_block_contents = plugins_block.group(1)
        plugins_block_contents += "\tid 'org.sonarqube' version '4.2.1.3168'\n"

        build_gradle_contents = build_gradle_contents.replace(plugins_block.group(1), plugins_block_contents)

    build_gradle_file.close()

    # Salve o arquivo em modo de escrita
    with open(build_gradle_location, "w") as output_file:
        output_file.write(build_gradle_contents)


PRS_FILE = f"./data/raw_data/sample_filtered_prs_{current_repo}.json"
SONAR_API_URL = "http://localhost:9000/api"
USERNAME = "admin"
PASSWORD = "YOUR-PASSWORD"
ISSUE_FIELDS = [
    "key",
    "rule",
    "severity",
    "component",
    "status",
    "debt",
    "type",
    "textRange",
]
COMMAND_TO_COMPILE = "mvn clean install -DskipTests -Dspotbugs.skip -Dcheckstyle.skip -DskipFormat -DverifyFormat -Dformatter.skip -Drat.skip=true"

input_file = open(PRS_FILE, "r")
prs_input = json.load(input_file)

create_exclude_prs_file()

prs = check_prs_to_process(prs_input)

# iterate in prs
for index in range(len(prs)):
    current_pr = prs[index]["pr_number"]

    def process_pr():

        # Create project and token
        current_sonar_token = create_sonar_token(current_pr)
        issues_json = f"./data/issues/issues_{current_repo}_{current_pr}.json"
        issues = []

        print(f"Current PR: {current_pr}")
        
        commits = [commit["sha"] for commit in prs[index]["commits"]]

        is_pr_commit_first = prs[index]["is_pr_commit_first"]
        

        if is_pr_commit_first:
            commits.insert(0, prs[index]["start_commit"])
        else:
            start_commit_index = [i for i, commit in enumerate(commits) if commit == prs[index]["start_commit"]][0]
            commits = commits[start_commit_index:]

        print(commits)

        project_url = f"https://www.github.com/apache/{current_repo}"

        print(f"Commits length: {len(commits)}")

        for i in range(len(commits)):
            commit_sha = commits[i]

            print(f"Current commit: {commit_sha}")

            print("Downloading commit...")
            download_commit(project_url, commit_sha)

            check_build_files(commit_sha)

            print("Compiling...")
            subprocess.call(
                f'chmod -R 777 {current_repo}-{commit_sha}', shell=True)
            result = subprocess.call(
                f"cd {current_repo}-{commit_sha} && {COMMAND_TO_COMPILE}", shell=True
            )

            if result != 0:
                shutil.rmtree(f"{current_repo}-{commit_sha}")
                error_msg = f"Failed to compile... PR: {current_pr}, commit: {commit_sha}"
                add_pr_to_exclude_prs(current_pr, error_msg)
                raise Exception(error_msg)

            sonar_command = f"mvn sonar:sonar -Dsonar.token={current_sonar_token}  \
                -Dsonar.projectKey={current_repo}-{current_pr} \
                -Dsonar.projectName='{current_repo}-{current_pr}' \
                -Dsonar.projectBaseDir='.' \
                -Dsonar.host.url=http://localhost:9000 \
                -Dsonar.login={USERNAME} \
                -Dsonar.password={PASSWORD}"

            print("Running sonar scan...")
            result = subprocess.call(
                f"cd {current_repo}-{commit_sha} && {sonar_command}", shell=True
            )

            if result != 0:
                shutil.rmtree(f"{current_repo}-{commit_sha}")
                error_msg = f"Failed to run sonar... PR: {current_pr}, commit: {commit_sha}"
                add_pr_to_exclude_prs(current_pr, error_msg)
                raise Exception(error_msg)


            # [{ "commit_sha": "21212...", "issues": [ { ... }, { ... } ]}]
            issues.append({"commit_sha": commit_sha, "issues": get_sonar_issues(current_pr)})
            shutil.rmtree(f"{current_repo}-{commit_sha}")

        with open(issues_json, "w") as issues_file:
            json.dump(issues, issues_file)

        print("end pr... \n\n")

        return

    try:
        process_pr()
    except Exception as error:
        delete_sonar_project(current_pr)
        print(print('\033[91m' + str(error) + '\033[0m'))
        traceback.print_exc()
        logging.exception("Ocorreu um erro:")
        exit()

