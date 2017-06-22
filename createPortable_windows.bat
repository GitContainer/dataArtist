REM create a portable version of dataArtist using 'pyinstaller'
REM the result is saved in /dist/dataArtist


rd /S /Q dist

rd /S /Q build

REM get parent dir
for %%x in ("%CD%") do set PARENT_DIR=%%~dpx
echo %PARENT_DIR%

REM mkdir _backup
REM COPY C:\Users\elkb4\Desktop\Programming\git\PROimgprocessor _backup
REM python obfuscateDir.py %PARENT_DIR%\PROimgprocessor\PROimgProcessor



pyinstaller createPortable_windows.spec

COPY packaging dist


REM python obfuscateDir.py %PARENT_DIR%\PROimgProcessor\PROimgProcessor done

REM would be cool to create azip file from all...
REM - this doesnt work: for /d %%a in (dist) do (ECHO zip -r -p "%%~na.zip" ".\%%a\*")