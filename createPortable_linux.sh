rm -rf dist
rm -rf build

python obfuscateDir.py /home/karl/git/PROimgprocessor/PROimgProcessor

pyinstaller createPortable_linux.spec

cp packaging dist

python obfuscateDir.py /home/karl/git/PROimgprocessor/PROimgProcessor/PROimgProcessor done
