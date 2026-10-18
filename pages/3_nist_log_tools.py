from contextlib import redirect_stdout
from pathlib import Path

import streamlit as st
from scripts.file_inp import get_folder, get_file
from scripts import nist_o_search, convert_nistlog_txt_to_tsv, convert_search_output_txt_to_tsv

st.set_page_config(layout="wide")


class StreamlitConsole:
    def __init__(self):
        self.output = ""
        self.box = st.empty()

    def write(self, text):
        self.output += text
        self.box.code(self.output, height=300)

    def flush(self):
        pass

tab1, tab2, tab3 = st.tabs(["nist_o_search", "nistlog_to_tsv", "search_output_to_tsv"])
with tab1:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select nist log Folder", key="nist_log_folder_button"):
                st.session_state.nist_log_folder = get_folder()

            if st.button("Select Save Folder", key="save_folder_fpm_button"):
                st.session_state.nist_save_folder = get_folder()

        folder_path = st.session_state.get("nist_log_folder", "")
        save_path = st.session_state.get("nist_save_folder", "")

        st.write("**Nist log folder:**", folder_path)
        st.write("**Save folder:**", save_path)

        chem_name = st.text_input("Chemical Name", key="chem_name")
    if st.button("Run nist_o_search", key="run_nist_o", type="primary"):
        df_out = nist_o_search.main(chem_name, folder_path, save_path)
        st.dataframe(df_out)
    st.write("docs here")
with tab2:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select nist log", key="nist_log_button_tsv"):
                st.session_state.nist_log_tsv = get_file()

            if st.button("Select Save Folder", key="save_folder_button_tsv"):
                st.session_state.nist_save_folder_tsv = get_folder()

        file_path = st.session_state.get("nist_log_tsv", "")
        save_path = st.session_state.get("nist_save_folder_tsv", "")

        st.write("**Nist log file path:**", file_path)
        st.write("**Save folder:**", save_path)

    if st.button("Convert", key="convert_nist_log_to_TSV", type="primary"):
        console = StreamlitConsole()

        with redirect_stdout(console):
            args = [file_path, "-o", save_path+"/"+Path(file_path).name+".tsv"]
            convert_nistlog_txt_to_tsv.main(args)

    st.write("this code processes full NIST search output log file into truncated file for creating calendar and hourly plots")
with tab3:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Data Folder", key="nist_data_folder_button_tsv"):
                st.session_state.nist_data_folder_tsv = get_folder()

            if st.button("Select Save Folder", key="nist_save_folder_button_tsv"):
                st.session_state.nist_save_folder_tsv_2 = get_folder()

        data_path = st.session_state.get("nist_data_folder_tsv", "")
        save_path = st.session_state.get("nist_save_folder_tsv_2", "")

        st.write("**NIST data folder:**", data_path)
        st.write("**Save folder:**", save_path)

        fail_on_error = st.checkbox("Fail on first error", value=False)

    if st.button("Convert", key="convert_nist_logs_to_TSV", type="primary"):
        console = StreamlitConsole()

        with redirect_stdout(console):
            args = [data_path, "-o", str(Path(save_path) / "search_output.tsv")]

            if fail_on_error:
                args.append("--fail-on-error")

            convert_search_output_txt_to_tsv.main(args)
    st.write("docs here -- problems with input")