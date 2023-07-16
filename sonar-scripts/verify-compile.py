import requests
import zipfile
import io
import subprocess
import shutil


def download_commit(project_url, commit_sha):
    commit_url = f"{project_url}/archive/{commit_sha}.zip"

    response = requests.get(commit_url, stream=True)

    zip = zipfile.ZipFile(io.BytesIO(response.content))
    zip.extractall()


current_repo = "accumulo"
project_url = f"https://github.com/apache/{current_repo}"
commit_sha = "5342f795b9799d6382e192e7b54d8212fa5a7bef"
commit_url = f"{project_url}/archive/{commit_sha}.zip"

COMMAND_TO_COMPILE = "mvn clean install -DskipTests -Dspotbugs.skip -Dcheckstyle.skip -DskipFormat -DverifyFormat -Dformatter.skip"

download_commit(project_url, commit_sha)

# process = subprocess.Popen(args, user=username)

print("Compiling...")
subprocess.call(f'chmod -R 777 {current_repo}-{commit_sha}', shell=True)

result = subprocess.call(
    f"cd {current_repo}-{commit_sha} && {COMMAND_TO_COMPILE}", shell=True)

if result != 0:
    raise Exception(
        f"Failed to compile... commit: {commit_sha}")

shutil.rmtree(f"{current_repo}-{commit_sha}")
