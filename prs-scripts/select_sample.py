import json
import os
import random

prs_directory = './data/raw_data/'
sample_size = 50

for dirpath, dirnames, filenames in os.walk(prs_directory):
    files = [file for file in filenames if ("lucene" in file or "accumulo" in file or "maven-surefire" in file or "commons-io" in file) and file.startswith(
        "filtered")]

    for file in files:
        file_path = os.path.join(dirpath, file)

        with open(file_path, "r") as input_file:
            prs = json.load(input_file)

            sample_prs = []

            if len(prs) < sample_size:
                sample_prs = prs
            else:
                sample_prs = random.sample(prs, sample_size)

            path_splited = file_path.split("/")
            path_splited[-1] = "sample_" + path_splited[-1]

            with open("/".join(path_splited), "w") as output:
                json.dump(sample_prs, output, indent=4)
