import os
import sys
import pandas as pd
import re
def main(chem_name, nist_o_folder, output_folder):
    hit_list = []

    def process_file(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            full_hit_list = f.read()
            split_hit_list = full_hit_list.split("Unknown: ")
            for ele in split_hit_list:
                print(ele)
            for section in split_hit_list:
                if chem_name in section:
                    lines = section.splitlines()

                    desc_line = lines[0]
                    split_desc_line = desc_line.split('|')

                    name_line = lines[1]
                    names = re.findall(r"<<(.*?)>>", name_line)

                    for name in names:
                        split_desc_line.insert(0, name)

                    hit_list.append(split_desc_line)

    for dirpath, dirnames, filenames in os.walk(nist_o_folder):
        for file in filenames:
            if file.endswith('.txt') or file.endswith('.TXT'):
                process_file(dirpath+'/'+file)
    print(f"List for chem name: {chem_name}")
    for ele in hit_list:
        print(ele)
    print("Saving csv")
    df = pd.DataFrame(hit_list)
    df.to_csv(output_folder+f"hit_list_{chem_name}.csv")

    return df
