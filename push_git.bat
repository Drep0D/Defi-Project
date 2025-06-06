@echo off
set /p mensaje=📝 Escribe el mensaje del commit: 
git add .
git commit -m "%mensaje%"
git push
pause