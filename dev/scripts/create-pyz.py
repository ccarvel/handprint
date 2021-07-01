#!/usr/bin/env python3
# =============================================================================
# @file    create-pyz
# @brief   Script to create Handprint executable zipapps using shiv
# @created 2021-06-25
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/handprint
#
# Preliminary setup (on macOS) assumed to have been done before this is run:
#   brew install python@3.8
#   brew install python@3.9
#   brew install pyenv
#   pyenv install 3.9.0  3.9.1  3.9.5
#   pyenv install 3.8.0  3.8.1  3.8.2  3.8.10
# =============================================================================

from   datetime import date
from   fastnumbers import isint
import pkg_resources
from   os import getcwd, chdir, system
from   os.path import exists, dirname, join, basename
from   rich.console import Console
import subprocess
from   subprocess import check_output, check_call
import sys
from   sys import exit
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED


# Constants used later.
# .............................................................................

# macOS Catalina (and probably later) systems ship with a /usr/bin/python3,
# but NOT a /usr/bin/python3.8.  The initial /usr/bin/python3 is a stub that
# offers to download and install Python the first time you run it.  What it
# installs still does not have an executable named "python3.8", only python3.
# Thus, we can't ask for an explicit x.y version of Python in the hash-bang
# line because that would always fail on Catalina unless the user installs a
# different distribution of Python.
#
# The executable created by shiv needs at least Python 3.6 because it uses
# f-strings internally.  If you try to run the shiv-produced result with an
# earlier version of Python, you get a syntax error and you have to be a
# Python expert to figure out what it means (namely, that your version of
# Python is too low).  There is no provision in shiv to do something like
# test the minimum version of Python in its bootstrap script, so if we want to
# give the user better information about why it fails on Python versions before
# 3.6, we have to find another solution.
#
# In addition, Handprint needs a minimum of Python 3.8.  Testing that would be
# easier; it could be done with a preamble script for shiv.  However, since we
# have to test the Python version right at the beginning anyway, we may as well
# just test for 3.8 as the minimum.
#
# The approach used here is to leverage shiv's option to include a custom
# hash-bang line, and use that to insert a short polyglot script that tests
# the version of Python and either exits with an error or execs Python on the
# whole file.  This code becomes the first few lines inside the Handprint
# zipapp.  The syntax for making this work is partly based on the 2016-03-02
# Stack Overflow posting at https://stackoverflow.com/a/35744488/743730.
#
# (Implementation note: the length of this hash-bang script is at the maximum
# character length accepted by shiv -- anything longer is rejected.  I would
# have wanted to write a better error message but it's not possible.)

_HASHBANG = r"""/bin/bash
''''test \$(python3 -V 2>&1|cut -c 10) -ge 8 && exec python3 -x \"\$0\" \"\$@\" # '''
''''exec echo 'Python too old.' # '''"""

_ZIP_COMMENTS_FMT = '''
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This Zip archive file was created on {0}. It includes
a self-contained, executable copy of Handprint ("Handwritten
Page Recognition Test") for Python version {2} on {3}
systems. To learn more about Handprint, please visit
https://github.com/caltechlibrary/handprint/.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''

_README_FMT = '''
About the Handprint version {1} distribution for {3}
=========================================================

The file named "handprint" inside the ZIP file that you
downloaded is an executable Python program in a special
format (not a script) that only needs an installation of
Python version {2} on your computer to run.

Simply move or copy "handprint" to a location where you
put other command-line programs on your computer.  A
popular location is /usr/local/bin/.  The following is an
example command that you can type in a terminal to move
"handprint" there:

    sudo mv handprint /usr/local/bin

To see usage information for "handprint", run it with the
-h option, like this:

    handprint -h

For more detailed help, particularly for how to install
credentials to use cloud services from Amazon, Google,
and Microsoft, please visit the website

    https://github.com/caltechlibrary/handprint

Thank you for your interest in Handprint, the HANDwritten
Page RecognitIoN Test!

Mike Hucka
california institute of Technology Library
{0}
'''


# Utility functions used below.
# .............................................................................

def run(cmd, quiet = False):
    if quiet:
        return check_output(cmd, shell = True).decode()
    else:
        return check_call(cmd, shell = True,
                          stdout = sys.stdout, stderr = subprocess.STDOUT)


def quit(msg):
    print(f'‼️  {msg}', flush = True)
    exit(1)


def inform(text):
    Console().print(text, style = "cyan")


# Sanity-check the run-time environment before attempting anything else.
# .............................................................................

here  = getcwd()
if not exists(join(here, 'requirements.txt')):
    quit(f'Expected to be in same directory as requirements.txt')

setup_file = join(here, 'setup.cfg')
if not exists(setup_file):
    quit(f'__init__.py does not exist in {setup_file}')

if len(sys.argv) < 2:
    quit(f'First argument must be destination where outputs will be written')

dest = sys.argv[1]
if not exists(dest):
    quit(f'Directory does not exist: {dest}')

if len(sys.argv) < 3:
    quit(f'Second argument must be the target Python version')

py_version = sys.argv[2]
if len(py_version.split('.')) < 3 or not all(isint(x) for x in py_version.split('.')):
    quit(f'Python version must be in the form x.y.z')

known_versions = [s.strip() for s in run('pyenv versions', True).split('\n')]
if py_version not in known_versions:
    quit(f'pyenv lacks version {py_version} -- run "pyenv install {py_version}"')


# Gather information.
# .............................................................................

py_short_version = '.'.join(py_version.split('.')[0:2])

with open('setup.cfg', 'r') as config_file:
    for line in config_file.readlines():
        if line.startswith('version'):
            h_version = line.split('=')[1].strip()

os      = run("uname -s | tr '[A-Z]' '[a-z]' | sed 's/darwin/macos/'", True).strip()
dirname = f'handprint{h_version}-{os}-python{py_short_version}'
outdir  = join(dest, dirname)
outname = f'handprint'
today   = str(date.today())


# Do the work.
# .............................................................................

inform(f'Creating output directory in {outdir}')
run(f'rm -rf {outdir}')
run(f'mkdir -p {outdir}')
chdir(outdir)

inform(f'Setting up pyenv local environment')
run(f'pyenv local {py_version}')
run(f'~/.pyenv/shims/pip install shiv --upgrade')

inform(f'Building output with shiv')

run(f'~/.pyenv/shims/shiv -p "{_HASHBANG}" -c handprint -o "{outname}" -E '
    + f'--prefer-binary handprint=={h_version}')

inform(f'Creating zip file')
zip_file = dirname + '.zip'
comment  = _ZIP_COMMENTS_FMT.format(today, h_version, py_version, os)
readme   = _README_FMT.format(today, h_version, py_version, os)
with zipfile.ZipFile(zip_file, 'w', ZIP_STORED) as zf:
    zf.write(outname, join(dirname, outname))
    zf.writestr(join(dirname, 'README-HANDPRINT-INSTRUCTIONS.txt'), readme)
    zf.comment = comment.encode()

inform(f'Done; output is in {outdir}')
