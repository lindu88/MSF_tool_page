from datetime import date
from pathlib import Path

import streamlit as st
from scripts import MSF_hourplot, MSF_calplot_tsv, MSF_ticplot_tsv, MSF_ticplot_sumplot_tsv
from scripts.file_inp import get_folder, get_file
st.set_page_config(layout="wide")



ndm, tab1, tab2, tab3, tab4 = st.tabs(["Null date maker", "MSF_calplot_tsv","MSF_ticplot_tsv","MSF_ticplot_sumplot_tsv", "MSF_hourplot_tsv"])
with ndm:
    if "date_ranges" not in st.session_state:
        st.session_state.date_ranges = []

    if "date_range_save_folder" not in st.session_state:
        st.session_state.date_range_save_folder = ""

    if st.button("Select Save Folder"):
        st.session_state.date_range_save_folder = get_folder()

    save_path = st.session_state.date_range_save_folder

    st.write("**Save folder:**", save_path)

    file_name = st.text_input("File Name", value="date_ranges.tsv")

    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date.today())

    if st.button("Add Range"):
        st.session_state.date_ranges.append((start_date, end_date))

    for start, end in st.session_state.date_ranges:
        st.write(start, end)

    if st.button("Remove Last Range"):
        if st.session_state.date_ranges:
            st.session_state.date_ranges.pop()

    if st.button("Save TSV", type="primary"):
        file_path = Path(save_path) / file_name

        with open(file_path, "w") as file:
            for start, end in st.session_state.date_ranges:
                file.write(f"{start}\t{end}\n")

        st.success(f"Saved to {file_path}")
with tab1:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Input File", key="input_file_button_MSF_calplot"):
                st.session_state.input_file_MSF_calplot = get_file()

            if st.button("Select Null Dates File", key="null_file_button_MSF_calplot"):
                st.session_state.null_file_MSF_calplot = get_file()

            if st.button("Select Save Folder", key="save_folder_button_MSF_calplot"):
                st.session_state.save_folder_MSF_calplot = get_folder()

        input_file = st.session_state.get("input_file_MSF_calplot", "")
        null_file = st.session_state.get("null_file_MSF_calplot", "")
        save_path = st.session_state.get("save_folder_MSF_calplot", "")

        st.write("**Input file:**", input_file)
        st.write("**Null dates file:**", null_file)
        st.write("**Save folder:**", save_path)

        site = st.text_input("Site", value="AMB", key="site_MSF_calplot")

    if st.button("Run MSF_calplot", key="run_MSF_calplot", type="primary"):
        args = [input_file,"--site", site,"--null-periods", null_file,"--save-dir", save_path,"--no-show"]

        figs, dfs = MSF_calplot_tsv.main(args)

        for fig, df in zip(figs, dfs):
            section = st.container()
            with section:
                st.pyplot(fig)
                st.dataframe(df)


    st.write("docs here")
with tab2:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Input File", key="input_file_button_MSF_ticplot_1"):
                st.session_state.input_file_MSF_ticplot_1 = get_file()

            if st.button("Select Null Dates File", key="null_file_button_MSF_ticplot_1"):
                st.session_state.null_file_MSF_ticplot_1 = get_file()

            if st.button("Select Output Folder", key="output_folder_button_MSF_ticplot_1"):
                st.session_state.output_folder_MSF_ticplot_1 = get_folder()

        input_file = st.session_state.get("input_file_MSF_ticplot_1", "")
        null_file = st.session_state.get("null_file_MSF_ticplot_1", "")
        output_folder = st.session_state.get("output_folder_MSF_ticplot_1", "")

        st.write("**Input file:**", input_file)
        st.write("**Null dates file:**", null_file)
        st.write("**Output folder:**", output_folder)

        output_name = st.text_input("Output File Name", value="",key="output_name_MSF_ticplot_1")

    if st.button("Run MSF_ticplot", key="run_MSF_ticplot_1", type="primary"):
        output_path = str(Path(output_folder) / output_name)

        args = [input_file, "--null-periods", null_file, "--output", output_path, "--no-show"]
        try:
            fig = MSF_ticplot_sumplot_tsv.main(args)
            st.pyplot(fig)
        except Exception as e:
            st.error(e)

    st.write("docs here")
with tab3:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Input File", key="input_file_button_MSF_ticplot_2"):
                st.session_state.input_file_MSF_ticplot_2 = get_file()

            if st.button("Select Null Dates File", key="null_file_button_MSF_ticplot_2"):
                st.session_state.null_file_MSF_ticplot_2 = get_file()

            if st.button("Select Output Folder", key="output_folder_button_MSF_ticplot_2"):
                st.session_state.output_folder_MSF_ticplot_2 = get_folder()

        input_file = st.session_state.get("input_file_MSF_ticplot_2", "")
        null_file = st.session_state.get("null_file_MSF_ticplot_2", "")
        output_folder = st.session_state.get("output_folder_MSF_ticplot_2", "")

        st.write("**Input file:**", input_file)
        st.write("**Null dates file:**", null_file)
        st.write("**Output folder:**", output_folder)

        output_name = st.text_input("Output File Name", value="",key="output_name_MSF_ticplot")

    if st.button("Run MSF_ticplot", key="run_MSF_ticplot_2", type="primary"):
        output_path = str(Path(output_folder) / output_name)

        args = [input_file, "--null-periods", null_file, "--output", output_path, "--no-show"]
        try:
            fig = MSF_ticplot_sumplot_tsv.main(args)
            st.pyplot(fig)
        except Exception as e:
            st.error(e)

    st.write("docs here")
with tab4:
    with st.container(border=True):
        with st.container(border=True, horizontal=True, horizontal_alignment="left"):
            if st.button("Select Input File", key="input_file_button_MSF_hourplot"):
                st.session_state.input_file_MSF_hourplot = get_file()

            if st.button("Select Save Folder", key="save_folder_button_MSF_hourplot"):
                st.session_state.save_folder_MSF_hourplot = get_folder()

        input_file = st.session_state.get("input_file_MSF_hourplot", "")
        save_path = st.session_state.get("save_folder_MSF_hourplot", "")

        st.write("**Input file:**", input_file)
        st.write("**Save folder:**", save_path)

        site = st.text_input("Site", value="AMB", key="site_MSF_hourplot")
        top_n = st.number_input("Top N", min_value=1, value=5, key="top_n_MSF_hourplot")
        title_suffix = st.text_input("Title Suffix", value="?", key="title_suffix_MSF_hourplot")

    if st.button("Run MSF_hourplot", key="run_MSF_hourplot", type="primary"):
        args = [input_file, "--site", site, "--top-n", str(top_n), "--title-suffix", title_suffix, "--save-dir",
                save_path, "--no-show"]

        figs, dfs = MSF_hourplot.main(args)

        for fig, df in zip(figs, dfs):
            section = st.container()
            with section:
                st.pyplot(fig)
                st.dataframe(df)

    st.write("docs here")