@echo off
cd /d "%~dp0\.."
python -m ab_toolkit all
start web\index.html
