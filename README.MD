#To build one dir(internals folder)-
python -m PyInstaller --noconfirm --clean --onedir --name MSF_Tool --collect-all streamlit --collect-all calplot --copy-metadata streamlit --add-data "app.py;." --add-data "pages;pages" --add-data "scripts;scripts" --add-data ".streamlit;.streamlit" run_app.py

#to build one exe-
python -m PyInstaller --noconfirm --clean --onefile --name MSF_Tool --collect-all streamlit --collect-all calplot --copy-metadata streamlit --add-data "app.py;." --add-data "pages;pages" --add-data "scripts;scripts" --add-data ".streamlit;.streamlit" run_app.py