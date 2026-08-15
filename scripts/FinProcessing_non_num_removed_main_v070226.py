import os
import re
from collections import defaultdict
def read_elu_fin_files(file_folder_path,folder_path_files, save_file_name, cutoff_msp_IS, sc_cutoff):
    #Get fin files in folder
    fin_files = [f for f in os.listdir(folder_path_files) if f.endswith('.FIN')]
    elu_files = [f for f in os.listdir(folder_path_files) if f.endswith('.ELU')]

    #make folder if does not exist
    os.makedirs(file_folder_path + save_file_name, exist_ok=True)

    sum_out = ""
    sum_out_cal = ""

    #If no fin files raise error
    if len(fin_files) == 0:
        raise FileNotFoundError('No .fin files found')
    with open(file_folder_path + "/" + save_file_name + "/" + "sc100-_fin" + ".msp", "w") as scp_file:
        for fin_file in fin_files:
            sum_is = 0
            file_path = os.path.join(folder_path_files, fin_file)
            name = fin_file.split('.')[0]
            name_parts = name.split('_')
            name = name + "_fin"
            print(f"processing: {name}")
            empty = True

            fin_content = ""

            #dict of lists to store different data with same key
            duplicate_data = defaultdict(list)

            try:
                with open(file_path, 'r') as file:
                    with open(file_folder_path + "/" + save_file_name + "/" + name + ".msp", "w") as o_file:
                        content = file.read()
                        # split into components and don't keep first part
                        split_content = content.split('************************')
                        split_content = split_content[1:]
                        for section in split_content:
                            #content = section_until_blank(section)
                            content = remove_non_num(section)
                            rt, is_, sc = parse_section(content)
                            if int(is_) >= cutoff_msp_IS and int(sc) > sc_cutoff:
                                empty = False
                                write_msp_fin(o_file, content, name)
                            elif int(is_) >= cutoff_msp_IS and int(sc) <= sc_cutoff:
                                write_msp_fin(scp_file, content, name)
                if empty:
                    os.remove(file_folder_path + "/" + save_file_name + "/" + name + ".msp")
            except Exception as e:
                print(f"Error processing {fin_file}: {str(e)}")
    with open(file_folder_path + "/" + save_file_name + "/" + "sc100-_elu" + ".msp", "w") as scp_file:
        for elu_file in elu_files:
            sum_is = 0
            file_path = os.path.join(folder_path_files, elu_file)
            name = elu_file.split('.')[0]
            name_parts = name.split('_')
            name = name + "_elu"
            d = defaultdict(list)
            d_msp = defaultdict(list)
            print(f"processing: {name}")
            try:
                empty = True
                with open(file_path, 'r') as file:
                    content = file.read()
                    # split into components and don't keep first part
                    split_content = re.split(r'\n\s*\n', content)
                    # Filter out any empty entries
                    split_content = [entry.strip() for entry in split_content if entry.strip()]
                    for section in split_content:
                        #unecessary but might as well use just incase
                        content = section_until_blank(section)
                        content = remove_non_num(content)
                        rt, is_, sc = parse_section(content)
                        if int(is_) >= cutoff_msp_IS and int(sc) > sc_cutoff:
                            sum_is += int(is_)
                            #write_msp_elu(o_file, content, name)
                            add_value(d_msp,  int(sc), (int(sc), int(is_), content, name))
                            empty = False
                        elif int(is_) >= cutoff_msp_IS and int(sc) <= sc_cutoff:
                            write_msp_elu(scp_file, content, name)
                        if int(sc) > sc_cutoff:
                            add_value(d, int(sc), (int(sc), int(is_)))
                for key, _ in d.items():
                    sum_is += max(is_ for sc, is_ in d[key])
                with open(file_folder_path + "/" + save_file_name + "/" + name + ".msp", "w") as o_file:
                    for key_msp, _ in d_msp.items():
                        best = max(d_msp[key_msp], key=lambda x: x[1])
                        sc, is_, content, name = best
                        write_msp_elu(o_file, content, name)
                if sum_is > 0:
                    sum_out += f"{name} Sum of peaks IS: {sum_is}\n"
                    sum_out_cal += f"{name} Sum of peaks IS: {sum_is}\n"
                    sum_out += f"Dictionary of duplicates by scan number:\n"
                    sum_out += d_to_string(d)
                if empty:
                    os.remove(file_folder_path + "/" + save_file_name + "/" + name + ".msp")
            except Exception as e:
                print(f"Error processing {elu_file}: {str(e)}")
    with open(file_folder_path + "/" + save_file_name + "/" + "sum_of_peaks" + ".txt", "w") as sp_file:
        sp_file.write(sum_out)
    with open(file_folder_path + "/" + save_file_name + "/" + "sum_of_peaks_cal" + ".txt", "w") as sp_file:
        sp_file.write(sum_out_cal)

    folder = file_folder_path + "/" + save_file_name

    with open(folder + "/concat_elu.msp", "w") as out:
        for file in os.listdir(folder):
            if file.endswith("_elu.msp"):
                with open(folder + "/" + file, "r") as f:
                    out.write(f.read())
                    out.write("\n")

def parse_section(section):
    # regex for RT and is_ sections
    rt_match = re.findall(r'RT\d+(?:\.\d+)?', section)[0]
    is__match = re.findall(r'IS\d+(?:\.\d+)?', section)[0]
    sc_match = re.findall(r'SC\d+(?:\.\d+)?', section)[0]

    if rt_match is [] or is__match is []:
        print(f"Error parsing {section}: no is_ or rt match")
        return None

    #regex for extracting digits
    rt = re.findall(r'\d+\.?\d*', rt_match)[0]
    is_ = re.findall(r'\d+', is__match)[0]
    sc = re.findall(r'\d+', sc_match)[0]

    return rt, is_, sc

def write_msp_fin(o_file, section, name):
    ext_spec = section.split("EXTRACTED SPECTRUM")
    ext_spec = ext_spec[1:]
    content = section_until_blank(ext_spec)

    new_name_section = f"|{name}|"

    lines = content.split('\n')
    if lines and lines[0].startswith("NAME:"):
        lines[0] = lines[0].replace("NAME:", f"NAME:{new_name_section}").replace("| |", "|")

    renamed = '\n'.join(lines)
    o_file.write(renamed)
    o_file.write("\n\n\n\n\n")
    return False
def d_to_string(d):
    out = ""
    for key, value in sorted(d.items()):
        values = " ".join(f"({sc},{is_})" for sc, is_ in value)
        out += f"{key}: {values}\n"
    return out
def write_msp_elu(o_file, content, name):
    new_name_section = f"|{name}|"

    lines = content.split('\n')
    if lines and lines[0].startswith("NAME:"):
        lines[0] = lines[0].replace("NAME:", f"NAME:{new_name_section}").replace("| |", "|")

    renamed = '\n'.join(lines)
    o_file.write(renamed)
    o_file.write("\n\n\n\n\n")

def remove_non_num(section):
    out = re.sub(r'\([^)]*[^0-9.,)\s][^)]*\)', '', section)
    count = len(re.findall(r'\(\d+,\d+\s*\)', out))

    out = re.sub(
        r'(NUM PEAKS:\s*)(\d+)',
        lambda m: m.group(1) + str(count),
        out
    )


    return out

def section_until_blank(section):
    if isinstance(section, list):
        section = '\n'.join(section)
    section = section.lstrip()
    lines = section.splitlines()
    kept = []
    for ln in lines:
        if not ln.strip():
            break
        kept.append(ln)
    return "\n".join(kept)

def add_value(d, sc, tup, delta=3):
    for key in sorted(d):
        if abs(sc - key) <= delta:
            d[key].append(tup)
            return
    d[sc].append(tup)

if __name__ == "__main__":
    
    file_folder_path = input("Enter absolute file path for save: ")
    source_path = input("Enter path for source data: ")
    
    save_folder_name = input("Enter save folder name: ")
    
    #make folder if does not exist
    os.makedirs(file_folder_path + "/" + save_folder_name, exist_ok=True)
    cutoff = input("Enter IS cutoff: ")
    
    
    #cutoff values
    cutoff_2025_2 = 15_032_010
    cutoff_2025_1 = 64_910_400
    cutoff_2024_1 = 48_742_820
    cutoff_2024_2 = 65_583_000
    cutoff_2023_1 = 111_938_000
    cutoff_2023_2 = 38_207_800
    cutoff_2023_3 = 64_001_000
    cutoff_2022 = 90_286_700
    
    read_elu_fin_files(file_folder_path, source_path, save_folder_name, int(cutoff), 100)

