# =========================================================================
# Copyright (C) 2016-2023 LOGPAI (https://github.com/logpai).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========================================================================

import os
import sys

import Brain
import pandas as pd

sys.path.append("..")

from utils.evaluator_ga import compute_grouping_accuracy
from utils.evaluator_pa import (
    calculate_parsing_accuracy,
    calculate_relaxed_parsing_accuracy,
    calculate_similarity_accuracy,
)
from utils.evaluator_fta import compute_template_level_accuracy

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


input_dir = "C:/Users/irfan/Logentum/loghub"
output_dir = "Brain_result/"


benchmark_settings = {
    "Proxifier": {
        "log_file": "Proxifier/Proxifier_2k.log",
        "log_format": r"\[<Time>\] <Program> - <Content>",
        "regex": [
            r"<\d+\ssec",
            r"([\w-]+\.)+[\w-]+(:\d+)?",
            r"\d{2}:\d{2}(:\d{2})*",
            r"[KGTM]B",
        ],
        "delimiter": [],
        "theshold": 20,
    },
    "HDFS": {
        "log_file": "HDFS/HDFS_2k.log",
        "log_format": "<Date> <Time> <Pid> <Level> <Component>: <Content>",
        "regex": [r"blk_-?\d+", r"(\d+\.){3}\d+(:\d+)?"],
        "delimiter": [],
        "theshold": 5,
    },
    "Hadoop": {
        "log_file": "Hadoop/Hadoop_2k.log",
        "log_format": r"<Date> <Time> <Level> \[<Process>\] <Component>: <Content>",
        "regex": [r"(\d+\.){3}\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "Spark": {
        "log_file": "Spark/Spark_2k.log",
        "log_format": "<Date> <Time> <Level> <Component>: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"\b[KGTM]?B\b", r"([\w-]+\.){2,}[\w-]+"],
        "delimiter": [],
        "theshold": 5,
    },
    "Zookeeper": {
        "log_file": "Zookeeper/Zookeeper_2k.log",
        "log_format": r"<Date> <Time> - <Level>  \[<Node>:<Component>@<Id>\] - <Content>",
        "regex": [r"(/|)(\d+\.){3}\d+(:\d+)?"],
        "delimiter": [],
        "theshold": 5,
    },
    "BGL": {
        "log_file": "BGL/BGL_2k.log",
        "log_format": "<Label> <Timestamp> <Date> <Node> <Time> <NodeRepeat> <Type> <Component> <Level> <Content>",
        "regex": [r"core\.\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "HPC": {
        "log_file": "HPC/HPC_2k.log",
        "log_format": "<LogId> <Node> <Component> <State> <Time> <Flag> <Content>",
        "regex": [r"=\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "Thunderbird": {
        "log_file": "Thunderbird/Thunderbird_2k.log",
        "log_format": r"<Label> <Timestamp> <Date> <User> <Month> <Day> <Time> <Location> <Component>(\[<PID>\])?: <Content>",
        "regex": [r"(\d+\.){3}\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "Windows": {
        "log_file": "Windows/Windows_2k.log",
        "log_format": "<Date> <Time>, <Level>                  <Component>    <Content>",
        "regex": [r"0x.*?\s"],
        "delimiter": [],
        "theshold": 5,
    },
    "Linux": {
        "log_file": "Linux/Linux_2k.log",
        "log_format": r"<Month> <Date> <Time> <Level> <Component>(\[<PID>\])?: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"\d{2}:\d{2}:\d{2}"],
        "delimiter": [],
        "theshold": 5,
    },
    "Android": {
        "log_file": "Android/Android_2k.log",
        "log_format": "<Date> <Time>  <Pid>  <Tid> <Level> <Component>: <Content>",
        "regex": [
            r"(/[\w-]+)+",
            r"([\w-]+\.){2,}[\w-]+",
            r"\b(\-?\+?\d+)\b|\b0[Xx][a-fA-F\d]+\b|\b[a-fA-F\d]{4,}\b",
        ],
        "delimiter": [],
        "theshold": 5,
    },
    "HealthApp": {
        "log_file": "HealthApp/HealthApp_2k.log",
        "log_format": r"<Time>\|<Component>\|<Pid>\|<Content>",
        "regex": [],
        "delimiter": [],
        "theshold": 5,
    },
    "Apache": {
        "log_file": "Apache/Apache_2k.log",
        "log_format": r"\[<Time>\] \[<Level>\] <Content>",
        "regex": [r"(\d+\.){3}\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "OpenSSH": {
        "log_file": "OpenSSH/OpenSSH_2k.log",
        "log_format": r"<Date> <Day> <Time> <Component> sshd\[<Pid>\]: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"([\w-]+\.){2,}[\w-]+"],
        "delimiter": [],
        "theshold": 5,
    },
    "OpenStack": {
        "log_file": "OpenStack/OpenStack_2k.log",
        "log_format": r"<Logrecord> <Date> <Time> <Pid> <Level> <Component> \[<ADDR>\] <Content>",
        "regex": [r"((\d+\.){3}\d+,?)+", r"/.+?\s", r"\d+"],
        "delimiter": [],
        "theshold": 5,
    },
    "Mac": {
        "log_file": "Mac/Mac_2k.log",
        "log_format": r"<Month>  <Date> <Time> <User> <Component>\[<PID>\]( \(<Address>\))?: <Content>",
        "regex": [r"([\w-]+\.){2,}[\w-]+"],
        "delimiter": [],
        "theshold": 5,
    },
}

benchmark_result = []

for dataset, setting in benchmark_settings.items():
    print("\n=== Evaluation on %s ===" % dataset)
    indir = os.path.join(input_dir, os.path.dirname(setting["log_file"]))
    log_file = os.path.basename(setting["log_file"])
    parser = Brain.LogParser(
        log_format=setting["log_format"],
        indir=indir,
        outdir=output_dir,
        rex=setting["regex"],
        delimeter=setting["delimiter"],
        threshold=setting["theshold"],
        logname=dataset,
    )
    parser.parse(log_file)

    groundtruth = pd.read_csv(os.path.join(indir, log_file + "_structured.csv"), dtype=str)
    parsedresult = pd.read_csv(os.path.join(output_dir, log_file + "_structured.csv"), dtype=str)
    groundtruth.fillna("", inplace=True)
    parsedresult.fillna("", inplace=True)

    ga, fga = compute_grouping_accuracy(groundtruth, parsedresult)
    pa = calculate_parsing_accuracy(groundtruth, parsedresult)
    sa = calculate_similarity_accuracy(groundtruth, parsedresult)
    rpa = calculate_relaxed_parsing_accuracy(groundtruth, parsedresult)
    identified_templates, ground_templates, fta, pta, rta = compute_template_level_accuracy(
        dataset, groundtruth, parsedresult
    )

    benchmark_result.append([
        dataset,
        ga,
        fga,
        pa,
        sa,
        rpa,
        fta,
        pta,
        rta,
        identified_templates,
        ground_templates,
    ])

print("\n=== Overall evaluation results ===")
df_result = pd.DataFrame(
    benchmark_result,
    columns=[
        "Dataset",
        "GA",
        "FGA",
        "PA",
        "SA",
        "RPA@0.7",
        "FTA",
        "PTA",
        "RTA",
        "identified_templates",
        "ground_templates",
    ],
)
df_result.set_index("Dataset", inplace=True)

average_row = df_result.mean(numeric_only=True).to_frame().T
average_row.index = ["Average"]
df_result = pd.concat([df_result, average_row])

print(df_result)
df_result.to_csv("Brain_bechmark_result.csv", float_format="%.6f")
