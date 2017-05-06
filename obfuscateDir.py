import os
import subprocess
import shutil
# import time
# import compileall


def obfuscateDir(p, opt=None):
    '''
    Some (proprietary) code I rather not share...
    Since Python is an interpreter-based system
    encrypting *.py files or sending binaries
    does not hinder reverse engineering.

    But i can make it harder - at least

        this fn replaces all py files in a folder
        with barely readable versions of the same functionality
    '''

    p2 = os.path.join(os.path.dirname(p) + '_obfuscated',
                      os.path.basename(p))
    if opt is None:
        # make backup
        #         name = os.path.basename(p) + '_obfuscated'

        #         p2 = os.path.join(os.path.dirname(p), name)
        if os.path.exists(p2):
            shutil.rmtree(p2, ignore_errors=True)

        shutil.copytree(p, p2)
#         except FileExistsError:
#
#
#             pass
#             # backup only exists if cresteExe failed.
#             # in this case [p] is still obfuscated and nothing
#             # needs to be done.
#             return
#             shutil.rmtree(p2)
#             time.sleep(1)#wait till tree is removed, so following works:
#             shutil.copytree(p, p2)

        for root, _, files in os.walk(p2, topdown=False):
            for name in files:
                # select only python files:
                if name != '__init__.py' and (name.endswith('.py') or
                                              name.endswith('.pyw')):
                    pp = os.path.join(root, name)
                    # replace current file with obfuscated version:
                    proc = subprocess.Popen(
                        #--obfuscate-builtins #break functionality...
                        #--obfuscate-variables --replacement-length=6
                        #breaks in GridDetection
                        # reason is ,that all fn(xx=xx) are ignored
                        "pyminifier -o %s %s" % (pp, pp), shell=True)
                    proc.wait()

                    # remove __main__ :
                    with open(pp, 'r') as f:
                        lines = f.readlines()
                        found = False
                        for n, l in enumerate(lines):
                            if "if __name__ == '__main__':" in l:
                                found = True
                                break
                        if found:
                            with open(pp, 'w') as f:
                                f.writelines(lines[:n])

                    # TODO: NEED TO MAKE PYC ONLY DISTRIBUTION WORK
                    # compileall.compile_file(pp)
                    # os.remove(pp)

    else:
        shutil.rmtree(os.path.dirname(p2), ignore_errors=True)
#         # restore backup
#         name = '_backup_' + os.path.basename(p)
#         p2 = os.path.join(os.path.dirname(p), name)
#         ###doesnt work####
#         shutil.rmtree(p, ignore_errors=True)
#         time.sleep(1)  # wait till tree is removed, so following works:
#         shutil.move(p2, p)


if __name__ == '__main__':

    #     pin = r'C:\Users\elkb4\Desktop\Programming\git\PROimgprocessor\PROimgProcessor\features\GridDetection.py'
    #     pout = r'C:\Users\elkb4\Desktop\Programming\git\PROimgprocessor\PROimgProcessor\features\GridDetection_new.py'
    #
    #     subprocess.Popen(
    #         #--obfuscate-builtins #break functionality...
    #         #--obfuscate-variables #breaks in GridDetection
    #         "pyminifier --obfuscate-variables --replacement-length=4 -o %s %s" % (pout, pin), shell=True)

    import sys
    obfuscateDir(*sys.argv[1:])
