REM create a portable version of dataArtist using 'pyinstaller'
REM the result is saved in /dist/dataArtist


rd /S /Q dist

rd /S /Q build

REM mkdir _backup
REM COPY C:\Users\elkb4\Desktop\Programming\git\PROimgprocessor _backup
python obfuscateDir.py C:\Users\elkb4\Desktop\Programming\git\PROimgprocessor\PROimgProcessor



pyinstaller createPortable_windows.spec

COPY packaging dist


python obfuscateDir.py C:\Users\elkb4\Desktop\Programming\git\PROimgProcessor\PROimgProcessor done

REM would be cool to create azip file from all...
REM - this doesnt work: for /d %%a in (dist) do (ECHO zip -r -p "%%~na.zip" ".\%%a\*")