import os
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
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
output_dir = "Drain3_result"

benchmark_settings = {
    "HDFS": {
        "log_file": "HDFS/HDFS_2k.log",
        "log_format": "<Date> <Time> <Pid> <Level> <Component>: <Content>",
        "regex": [r"blk_-?\d+", r"(\d+\.){3}\d+(:\d+)?"],
    },
    "Hadoop": {
        "log_file": "Hadoop/Hadoop_2k.log",
        "log_format": r"<Date> <Time> <Level> \[<Process>\] <Component>: <Content>",
        "regex": [r"(\d+\.){3}\d+"],
    },
    "Spark": {
        "log_file": "Spark/Spark_2k.log",
        "log_format": "<Date> <Time> <Level> <Component>: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"\b[KGTM]?B\b", r"([\w-]+\.){2,}[\w-]+"],
    },
    "Zookeeper": {
        "log_file": "Zookeeper/Zookeeper_2k.log",
        "log_format": r"<Date> <Time> - <Level>  \[<Node>:<Component>@<Id>\] - <Content>",
        "regex": [r"(/|)(\d+\.){3}\d+(:\d+)?"],
    },
    "BGL": {
        "log_file": "BGL/BGL_2k.log",
        "log_format": "<Label> <Timestamp> <Date> <Node> <Time> <NodeRepeat> <Type> <Component> <Level> <Content>",
        "regex": [r"core\.\d+"],
    },
    "HPC": {
        "log_file": "HPC/HPC_2k.log",
        "log_format": "<LogId> <Node> <Component> <State> <Time> <Flag> <Content>",
        "regex": [r"=\d+"],
    },
    "Thunderbird": {
        "log_file": "Thunderbird/Thunderbird_2k.log",
        "log_format": r"<Label> <Timestamp> <Date> <User> <Month> <Day> <Time> <Location> <Component>(\[<PID>\])?: <Content>",
        "regex": [r"(\d+\.){3}\d+"],
    },
    "Windows": {
        "log_file": "Windows/Windows_2k.log",
        "log_format": "<Date> <Time>, <Level>                  <Component>    <Content>",
        "regex": [r"0x.*?\s"],
    },
    "Linux": {
        "log_file": "Linux/Linux_2k.log",
        "log_format": r"<Month> <Date> <Time> <Level> <Component>(\[<PID>\])?: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"\d{2}:\d{2}:\d{2}"],
    },
    "Android": {
        "log_file": "Android/Android_2k.log",
        "log_format": "<Date> <Time>  <Pid>  <Tid> <Level> <Component>: <Content>",
        "regex": [
            r"(/[\w-]+)+",
            r"([\w-]+\.){2,}[\w-]+",
            r"\b(\-?\+?\d+)\b|\b0[Xx][a-fA-F\d]+\b|\b[a-fA-F\d]{4,}\b",
        ],
    },
    "HealthApp": {
        "log_file": "HealthApp/HealthApp_2k.log",
        "log_format": r"<Time>\|<Component>\|<Pid>\|<Content>",
        "regex": [],
    },
    "Apache": {
        "log_file": "Apache/Apache_2k.log",
        "log_format": r"\[<Time>\] \[<Level>\] <Content>",
        "regex": [r"(\d+\.){3}\d+"],
    },
    "Proxifier": {
        "log_file": "Proxifier/Proxifier_2k.log",
        "log_format": r"\[<Time>\] <Program> - <Content>",
        "regex": [
            r"<\d+\ssec",
            r"([\w-]+\.)+[\w-]+(:\d+)?",
            r"\d{2}:\d{2}(:\d{2})*",
            r"[KGTM]B",
        ],
    },
    "OpenSSH": {
        "log_file": "OpenSSH/OpenSSH_2k.log",
        "log_format": r"<Date> <Day> <Time> <Component> sshd\[<Pid>\]: <Content>",
        "regex": [r"(\d+\.){3}\d+", r"([\w-]+\.){2,}[\w-]+"],
    },
    "OpenStack": {
        "log_file": "OpenStack/OpenStack_2k.log",
        "log_format": r"<Logrecord> <Date> <Time> <Pid> <Level> <Component> \[<ADDR>\] <Content>",
        "regex": [r"((\d+\.){3}\d+,?)+", r"/.+?\s", r"\d+"],
    },
    "Mac": {
        "log_file": "Mac/Mac_2k.log",
        "log_format": r"<Month>  <Date> <Time> <User> <Component>\[<PID>\]( \(<Address>\))?: <Content>",
        "regex": [r"([\w-]+\.){2,}[\w-]+"],
    },
}


def generate_logformat_regex(log_format: str):
    headers = []
    splitters = re.split(r"(<[^<>]+>)", log_format)
    regex = ""
    for index, splitter in enumerate(splitters):
        if index % 2 == 0:
            splitter = re.sub(" +", r"\\s+", splitter)
            regex += splitter
        else:
            header = splitter.strip("<>")
            regex += f"(?P<{header}>.*?)"
            headers.append(header)
    return headers, re.compile("^" + regex + "$")


def dataset_specific_cleanup(text: str, dataset: str) -> str:
    if dataset == "HealthApp":
        text = re.sub(":", ": ", text)
        text = re.sub("=", "= ", text)
        text = re.sub(r"\|", "| ", text)
    if dataset == "Android":
        text = re.sub(r"\(", "( ", text)
        text = re.sub(r"\)", ") ", text)
        text = re.sub(":", ": ", text)
        text = re.sub("=", "= ", text)
    if dataset == "HPC":
        text = re.sub("=", "= ", text)
        text = re.sub("-", "- ", text)
        text = re.sub(":", ": ", text)
    if dataset == "BGL":
        text = re.sub("=", "= ", text)
        text = re.sub(r"\.\.", ".. ", text)
        text = re.sub(r"\(", "( ", text)
        text = re.sub(r"\)", ") ", text)
    if dataset == "Hadoop":
        text = re.sub("_", "_ ", text)
        text = re.sub(":", ": ", text)
        text = re.sub("=", "= ", text)
        text = re.sub(r"\(", "( ", text)
        text = re.sub(r"\)", ") ", text)
    if dataset in {"HDFS", "Linux", "Spark", "Thunderbird"}:
        text = re.sub(":", ": ", text)
    if dataset == "Linux":
        text = re.sub("=", "= ", text)
    if dataset == "Windows":
        text = re.sub(":", ": ", text)
        text = re.sub("=", "= ", text)
        text = re.sub(r"\[", "[ ", text)
        text = re.sub(r"]", "] ", text)
    if dataset == "Zookeeper":
        text = re.sub(":", ": ", text)
        text = re.sub("=", "= ", text)
    if dataset == "OpenStack":
        text = re.sub(":", ": ", text)
    return text


def preprocess_content(content: str, regex_list, dataset: str) -> str:
    text = content
    for pattern in regex_list:
        text = re.sub(pattern, "<*>", text)
    text = dataset_specific_cleanup(text, dataset)
    return text


def parse_with_log_format(log_path: str, log_format: str):
    headers, pattern = generate_logformat_regex(log_format)
    rows = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
        for line_id, line in enumerate(handle, start=1):
            match = pattern.search(line.strip())
            if not match:
                continue
            row = {"LineId": line_id}
            for header in headers:
                row[header] = match.group(header)
            rows.append(row)
    return pd.DataFrame(rows)


def run_dataset(dataset: str, setting: dict):
    print(f"\n=== Evaluation on {dataset} ===")
    indir = os.path.join(input_dir, os.path.dirname(setting["log_file"]))
    log_file = os.path.basename(setting["log_file"])
    log_path = os.path.join(indir, log_file)

    config = TemplateMinerConfig()
    config.load(str(Path(__file__).resolve().parent / "examples" / "drain3.ini"))
    config.profiling_enabled = False
    template_miner = TemplateMiner(config=config)

    parsed_df = parse_with_log_format(log_path, setting["log_format"])
    if "Content" not in parsed_df.columns:
        raise ValueError(f"Log format for {dataset} must contain <Content>.")

    event_ids = []
    event_templates = []
    for content in parsed_df["Content"].tolist():
        preprocessed = preprocess_content(content, setting["regex"], dataset)
        result = template_miner.add_log_message(preprocessed)
        event_ids.append(f"E{result['cluster_id']}")
        event_templates.append(str(result["template_mined"]))

    parsed_df["EventId"] = event_ids
    parsed_df["EventTemplate"] = event_templates

    os.makedirs(output_dir, exist_ok=True)
    structured_out = os.path.join(output_dir, log_file + "_structured.csv")
    parsed_df.to_csv(structured_out, index=False, escapechar="\\", quoting=1)

    template_counts = Counter(event_templates)
    template_rows = [[f"E{i}", tmpl, count] for i, (tmpl, count) in enumerate(template_counts.items())]
    templates_out = os.path.join(output_dir, log_file + "_templates.csv")
    pd.DataFrame(template_rows, columns=["EventId", "EventTemplate", "Occurrences"]).to_csv(
        templates_out, index=False, escapechar="\\", quoting=1
    )

    groundtruth = pd.read_csv(os.path.join(indir, log_file + "_structured.csv"), dtype=str)
    parsedresult = pd.read_csv(structured_out, dtype=str)
    groundtruth.fillna("", inplace=True)
    parsedresult.fillna("", inplace=True)

    ga, fga = compute_grouping_accuracy(groundtruth, parsedresult)
    pa = calculate_parsing_accuracy(groundtruth, parsedresult)
    sa = calculate_similarity_accuracy(groundtruth, parsedresult)
    rpa = calculate_relaxed_parsing_accuracy(groundtruth, parsedresult)
    identified_templates, ground_templates, fta, pta, rta = compute_template_level_accuracy(
        dataset, groundtruth, parsedresult
    )

    return [dataset, ga, fga, pa, sa, rpa, fta, pta, rta, identified_templates, ground_templates]


if __name__ == "__main__":
    benchmark_result = []
    for dataset, setting in benchmark_settings.items():
        benchmark_result.append(run_dataset(dataset, setting))

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
    df_result.to_csv("Drain3_bechmark_result.csv", float_format="%.6f")
