@echo off
set SOURCE=d:\work\ai\project\taekwondo-poomase-1-5-2026\pose_landmarker.task
set DEST=D:\work\android\taekwondo_poomsae\app\src\main\assets\pose_landmarker.task
if exist "%SOURCE%" (
    echo Copying model file...
    copy "%SOURCE%" "%DEST%"
    echo Done.
) else (
    echo Source model file not found!
)
pause
