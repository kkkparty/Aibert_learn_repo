import argparse
import json
#python3 -m  fastchat.data.prepare_all --prefix /data/share_gpt_process/HTML_raw/ --model-name-or-path /data/Baichuan-7B 
def merge_json_files(file1, file2, output_file):
    # 读取第一个 JSON 文件
    with open(file1, 'r') as f1:
        data1 = json.load(f1)

    # 读取第二个 JSON 文件
    with open(file2, 'r') as f2:
        data2 = json.load(f2)

    # 拼接两个 JSON 数据
    combined_data = data1 + data2

    # 将拼接后的数据写入新的 JSON 文件
    with open(output_file, 'w') as combined_file:
        json.dump(combined_data, combined_file, indent=2)  # indent用于美化输出格式

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge two JSON files.")
    parser.add_argument("--file1", required=True, help="Path to the first JSON file.")
    parser.add_argument("--file2", required=True, help="Path to the second JSON file.")
    parser.add_argument("--output", required=True, help="Path to the output merged JSON file.")
    args = parser.parse_args()

    merge_json_files(args.file1, args.file2, args.output)

