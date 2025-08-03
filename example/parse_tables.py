from pathlib import Path
import re
import csv
from collections import Counter

def filter_odd_elements(lines):
    # remove all sublist with not 2 elements, keep a count of the number of odd elements
    filtered_lines = []
    odd_count = 0
    for sublist in lines:
        if len(sublist) == 2:
            filtered_lines.append(sublist)
        else:
            odd_count += 1
    return filtered_lines, odd_count

def clean_list(lines):
    remove_keywords = ["---", "\n", ""]
    # remove all elements in the sublsit that are empty, just "\n", "---"
    # also strip the elements in the sublist
    lines = [[element.strip().replace('"', "") for element in sublist if element.strip() not in remove_keywords] for sublist in lines]
    # remove empty sublists
    lines = [sublist for sublist in lines if sublist]
    return lines

def split_when_both_seen(data):
    delimiters = {'---\n', 'X\n'}
    result = []
    current = []
    seen = set()
    for item in data:
        if item in delimiters:
            seen.add(item)
            # 如果已经都出现过至少一次，就分隔
            if seen == delimiters:
                if current:
                    result.append(current)
                    current = []
                seen.clear()  # 重置计数
        else:
            current.append(item)
            seen.clear()  # 遇到正常内容，重置已见的分隔符集合
    if current:
        result.append(current)
    return result

def clean_content(lines):
    """
    Remove lines containing any of the following substrings:
    'Alias', 'Name', 'P11 P10', 'Available in Databank', '===== PAGE', 'Databank', 'Pure Component'
    """
    remove_keywords = [
        "Alias",
        "Name",
        "P11 P10",
        "Available in Databank",
        "===== PAGE",
        "Databank",
        "Pure Component",
        "Physical Property Data 11.1",
        "Fluid"
    ]
    cleaned_lines = []
    for line in lines:
        if any(keyword in line for keyword in remove_keywords):
            continue
        cleaned_lines.append(line)
    return cleaned_lines

# Directory containing all the table files
tables_dir = Path("example/data/tables")

# Get all table files (e.g., table_01.txt, table_02.txt, ...)
table_files = sorted(tables_dir.glob("table_*.txt"))

# Collect all pairs and odd counts
all_pairs = []
total_odd_count = 0
alias_lengths = []

for table_file in table_files:
    with open(table_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        lines = clean_content(lines)
        pairs = split_when_both_seen(lines)
        pairs = clean_list(pairs)
        filtered_pairs, odd_count = filter_odd_elements(pairs)
        total_odd_count += odd_count
        all_pairs.extend(filtered_pairs)
        # Collect alias lengths
        alias_lengths.extend([len(sublist[0]) for sublist in filtered_pairs])

# Write all pairs to CSV
output_csv = Path("example/data/final_table.csv")
output_csv.parent.mkdir(parents=True, exist_ok=True)
with open(output_csv, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["alias", "name"])
    for alias, name in all_pairs:
        writer.writerow([alias, name])

print(f"Total count of sublists with not exactly two elements: {total_odd_count}")
print(f"Total count of pairs: {len(all_pairs)}")
print("Alias length counts (dict):")
alias_length_counts = dict(Counter(alias_lengths))
print(alias_length_counts)

# Calculate and print percentage of alias length > 8
if alias_lengths:
    count_gt_8 = sum(1 for l in alias_lengths if l > 8)
    percent_gt_8 = (count_gt_8 / len(alias_lengths)) * 100
    print(f"Percentage of alias length > 8: {percent_gt_8:.2f}%")
else:
    print("No aliases found to calculate percentage.")

# Calculate and print percentage of pairs where both alias and name have length > 8
if all_pairs:
    count_both_gt_8 = sum(1 for alias, name in all_pairs if len(alias) > 8 and len(name) > 8)
    percent_both_gt_8 = (count_both_gt_8 / len(all_pairs)) * 100
    print(f"Percentage of pairs where both alias and name have length > 8: {percent_both_gt_8:.2f}%")
else:
    print("No pairs found to calculate percentage where both alias and name have length > 8.")