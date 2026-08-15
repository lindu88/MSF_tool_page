
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def read_fin_files(folder_path, save_path):
    df_calib, df_cyl = None, None

    fin_files = [f for f in os.listdir(folder_path) if f.endswith('.FIN')]

    if len(fin_files) == 0:
        raise FileNotFoundError('No .fin files found')

    names_CALIB = []
    benzene_rt_CALIB, benzene_is_CALIB = [], []
    decane_rt_CALIB, decane_is_CALIB = [], []
    hexane_rt_CALIB, hexane_is_CALIB = [], []

    names_CYL = []
    benzene_rt_CYL, benzene_is_CYL = [], []
    decane_rt_CYL, decane_is_CYL = [], []
    hexane_rt_CYL, hexane_is_CYL = [], []

    for fin_file in fin_files:
        file_path = os.path.join(folder_path, fin_file)
        name = str(file_path)
        filename = re.search(r'[^\\/]+(?:\.[^\\/]+)*$', name).group()

        is_calib = "CALIB" in name
        is_cyl = "CYL" in name

        if not (is_calib or is_cyl):
            print(f"Skipping (not CYL or CALIB): {filename}")
            continue

        print(f"processing: {name}")

        try:
            with open(file_path, 'r') as file:
                content = file.read()
                split_content = content.split('************************')[1:]

                benzene_values = []
                decane_values = []
                hexane_values = []

                for section in split_content:
                    content = section_until_blank(section)
                    if "|NABenzene\n|" in content:
                        rt, is_ = parse_section(content)
                        print(f"b : {rt}, {is_}")
                        benzene_values.append((rt, is_))
                    if "|NADecane\n|" in content:
                        rt, is_ = parse_section(content)
                        print(f"d : {rt}, {is_}")
                        decane_values.append((rt, is_))
                    if "|NAn-Hexane\n|" in content:
                        rt, is_ = parse_section(content)
                        print(f"h : {rt}, {is_}")
                        hexane_values.append((rt, is_))

                benzene_max = max(benzene_values, key=lambda x: x[1], default=(0.0, 0.0))
                decane_max = max(decane_values, key=lambda x: x[1], default=(0.0, 0.0))
                hexane_max = max(hexane_values, key=lambda x: x[1], default=(0.0, 0.0))

                if is_calib:
                    names_CALIB.append(filename)
                    benzene_rt_CALIB.append(benzene_max[0])
                    benzene_is_CALIB.append(benzene_max[1])
                    decane_rt_CALIB.append(decane_max[0])
                    decane_is_CALIB.append(decane_max[1])
                    hexane_rt_CALIB.append(hexane_max[0])
                    hexane_is_CALIB.append(hexane_max[1])

                elif is_cyl:
                    names_CYL.append(filename)
                    benzene_rt_CYL.append(benzene_max[0])
                    benzene_is_CYL.append(benzene_max[1])
                    decane_rt_CYL.append(decane_max[0])
                    decane_is_CYL.append(decane_max[1])
                    hexane_rt_CYL.append(hexane_max[0])
                    hexane_is_CYL.append(hexane_max[1])

        except Exception as e:
            print(f"Error processing {fin_file}: {str(e)}")

    if len(names_CALIB) > 0:
        df_calib = pd.DataFrame({
            'filename': names_CALIB,
            'benzene_rt': benzene_rt_CALIB,
            'benzene_is_': benzene_is_CALIB,
            'decane_rt': decane_rt_CALIB,
            'decane_is_': decane_is_CALIB,
            'hexane_rt': hexane_rt_CALIB,
            'hexane_is_': hexane_is_CALIB
        })
        df_calib.to_csv(os.path.join(save_path, "calib_results.csv"), index=False)
        print(f"Saved {len(names_CALIB)} CALIB entries to 'calib_results.csv'")

    if len(names_CYL) > 0:
        df_cyl = pd.DataFrame({
            'filename': names_CYL,
            'benzene_rt': benzene_rt_CYL,
            'benzene_is_': benzene_is_CYL,
            'decane_rt': decane_rt_CYL,
            'decane_is_': decane_is_CYL,
            'hexane_rt': hexane_rt_CYL,
            'hexane_is_': hexane_is_CYL
        })
        df_cyl.to_csv(os.path.join(save_path, "cyl_results.csv"), index=False)
        print(f"Saved {len(names_CYL)} CYL entries to 'cyl_results.csv'")

    return df_calib, df_cyl
def parse_section(section):
    # regex for RT and is_ sections
    rt_match = re.findall(r'RT\d+(?:\.\d+)?', section)[0]
    is__match = re.findall(r'IS\d+(?:\.\d+)?', section)[0]

    if rt_match is [] or is__match is []:
        print(f"Error parsing {section}: no is_ or rt match")
        return None

    #regex for extracting digits
    rt = re.findall(r'\d+\.\d{2}', rt_match)[0]
    is_ = re.findall(r'\d+', is__match)[0]

    return rt, is_

def section_until_blank(section):
    section = section.lstrip()
    lines = section.splitlines()
    kept = []
    for ln in lines:
        if not ln.strip():
            break
        kept.append(ln)
    return "\n".join(kept)

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing .fin files: ")
    save_path = input("Enter the save path: ")
    read_fin_files(folder_path, save_path)