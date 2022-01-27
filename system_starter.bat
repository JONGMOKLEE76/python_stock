@echo off

:init
@echo Started: %date% %time%
echo init starts
cd C:\Users\JONGMIN\Desktop\python_stock
@taskkill /f /im "python.exe"
set loop=0
set max_loop=300

:loop
set /a loop+=1
echo %loop%
timeout 2 > NUL
if %loop%==%max_loop% goto init
if %loop%==1 goto starter
if not %loop%==1 goto loop

:starter
start python main.py
timeout 10 > NUL
goto loop