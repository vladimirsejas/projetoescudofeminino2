@echo off

cd /d C:\projetoescudofeminino2

start "" cmd /k "py -m streamlit run dashboard\app.py"

timeout /t 4 /nobreak > nul

start "" http://localhost:8501
