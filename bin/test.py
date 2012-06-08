import argparse
import logtail
import os

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument(
    '--glob','-g',
    type=str,
    required="True",
    dest="fileglob",
    help="A file glob to help find files that need to be tailed.")

arg_parser.add_argument(
    '--directory','-d',
    type=str,
    required="True",
    dest="filedirectory",
    help="The directory to search for files.")

arg_parser.add_argument(
    '--debug','-D',
    action="store_true",
    dest="debug",
    default=False,
    help="Turn on debugging output.")

arg_parser.add_argument(
    "--single-file",'-s',
    action="store_true",
    dest="singlefile",
    default=False,
    help="Use when running a single rotating file (sys.log, for instance).")

arg_parser.add_argument(
    '--recovery-file','-r',
    type=str,
    dest="recovery_file",
    default=None,
    help="The file that will be used for recovery in multifile parsing.")

options = arg_parser.parse_args()

if options.debug == True :
    print options

if os.path.isdir(options.filedirectory) == True :
    lt = logtail.logtail(
        directory=options.filedirectory,
        globstr=options.fileglob,
        debug=options.debug,
        recovery_file=options.recovery_file,
        singlefile=options.singlefile)
    lt.run()
