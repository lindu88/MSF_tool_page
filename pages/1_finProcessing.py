import os
import pathlib
from logging import exception

import streamlit as st
from scripts import FinProcessing_master_v071526 as fpm
from scripts import FinProcessing_non_num_removed_main_v070226 as fpnnr
from scripts.file_inp import get_folder
import tkinter as tk
from tkinter import filedialog
from contextlib import redirect_stdout

st.set_page_config(layout="wide")
col1, col2 = st.columns(2)
class StreamlitConsole:
    def __init__(self):
        self.output = ""
        self.box = st.empty()

    def write(self, text):
        self.output += text
        self.box.code(self.output, height=300)

    def flush(self):
        pass


with col1:
    df_calib, df_cyl = None, None
    with st.container(border=True):
        st.subheader("FPM Processing")

        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select FIN Folder", key="fin_folder_fpm"):
                st.session_state.folder_path_fpm = get_folder()

            if st.button("Select Save Folder", key="save_folder_fpm"):
                st.session_state.save_path_fpm = get_folder()

        folder_path = st.session_state.get("folder_path_fpm", "")
        save_path = st.session_state.get("save_path_fpm", "")

        st.write("**FIN folder:**", folder_path)
        st.write("**Save folder:**", save_path)

        if st.button("Run FPM", key="run_fpm", type="primary"):
            console = StreamlitConsole()

            with redirect_stdout(console):
                try:
                    with st.spinner("Executing function, please wait..."):
                        df_calib, df_cyl= fpm.read_fin_files(folder_path, save_path)
                    st.success(f"Success")
                except Exception as e:
                    st.error(e)
    st.write("This code takes AMDIS-created *.fin files (AMDIS calibration library matches) and extracts Benzene, Hexane, and Decane areas for plotting and determination of xx ppb area value. This value can be applied as a detection cutoff.")
    st.dataframe(df_calib)
    st.dataframe(df_cyl)
with col2:
    with st.container(border=True):
        st.subheader("FPNNR Processing")

        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Source Data", key="source_data_fpnnr"):
                st.session_state.source_path_fpnnr = get_folder()

            if st.button("Select Save Path", key="save_path_fpnnr"):
                st.session_state.file_folder_path_fpnnr = get_folder()

        file_folder_path = st.session_state.get("file_folder_path_fpnnr", "")
        source_path = st.session_state.get("source_path_fpnnr", "")

        st.write("**Source path:**", source_path)
        st.write("**Save path:**", file_folder_path)


        def handle_cutoff_change():
            new_cutoff = st.session_state.cutoff_fpnnr
            new_scan_count = st.session_state.scan_count_cutoff_fpnnr

        cutoff = st.number_input("IS cutoff",step=1,key="cutoff_fpnnr", on_change=handle_cutoff_change)

        scan_count_cutoff = st.number_input("Scan count cutoff",min_value=1,value=100,step=1,key="scan_count_cutoff_fpnnr", on_change=handle_cutoff_change)

        if st.button("Run FPNNR", key="run_fpnnr", type="primary"):
            folder_name = f"fin_elu_processing_{pathlib.Path(source_path).name}_areac_{cutoff}_sc{scan_count_cutoff}"
            os.makedirs(os.path.join(file_folder_path, folder_name), exist_ok=True)

            console = StreamlitConsole()

            with redirect_stdout(console):
                try:
                    with st.spinner("Executing function, please wait..."):
                        fpnnr.read_elu_fin_files(file_folder_path, source_path, folder_name, int(cutoff),int(scan_count_cutoff))
                    st.success(f"Success")
                except Exception as e:
                    st.error(e)
    st.write("This code removes scans (typically air peak) early in chromatogram, and applies the area cutoff so that only peaks higher than area cutoff are searched through NIST library.")
