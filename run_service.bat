@echo off
REM -----------------------------------------------
REM Activate virtual environment and run Django server
REM -----------------------------------------------

REM Go to project folder
cd /d D:\My-Projects\ANTIGRAVITY\CRM   REM <-- CHANGE to your path

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Django server in background
start "" python serve.py
