import glob
import gzip
import os
import time
import argparse

class logtail(object):
    """
    This class can be used to tail a file and do something when new lines appear
    in it for logging.

    A typical usage case for this file might look like:

    python logtail.py --glob="auth.log" --directory="/var/log/" --single-file

    For a file that doesn't rotate or:

    python logtail.py --glob="apache2_access.*" --directory="/var/log/apache2/"

    For something that does rotate
    """
    def __init__(self,globstr,directory,debug,singlefile,readsize=10000,recovery_file=None):
        self._glob = globstr
        self._directory = directory
        self._singlefile = singlefile
        self._debug = debug
        self._handle_gz = True
        self._freshstart = False
        self._recovery_file = recovery_file
        self._readsize = readsize

    @property
    def readsize(self):
        """
        This determines how many bytes are read from a file at a time.
        """
        return self._readsize

    @readsize.setter
    def readsize(self,value):
        self._readsize = value

    @property
    def globstr(self):
        """
        This contains the glob string that will be used for searching for files to parse.
        It will be assumed that there should be an ordered list of files resulting from
        the  directory/globstr combination unless the property 'singlefile' is set.
        """
        return self._glob

    @globstr.setter
    def globstr(self, value):
        self._glob = value

    @property
    def directory(self):
        """
        The directory where we will search for matching files.
        """
        return self._directory

    @directory.setter
    def directory(self, value):
        self._directory = value 

    @property
    def recovery_file(self):
        """
        The file that will remember the last file read for multifile read recovery.
        """
        return self._recovery_file

    @recovery_file.setter
    def recovery_file(self, value):
        self._recovery_file = value 

    @property
    def singlefile(self):
        """
        If the globstr results in an absolute match, then this property should be set.
        This would be optimal for files like sys.log, where only one file rotates, but
        the current file only has one name.
        """
        return self._singlefile

    @singlefile.setter
    def singlefile(self, value):
        self._singlefile = value

    @property
    def debug(self):
        """Set for debug output."""
        return self._debug

    @debug.setter
    def debug(self,value):
        self._debug = value

    @property
    def handle_gz(self):
        """
        When apache2 rotates its files, it often gzips them.  This allows the tailer
        to treat gzip files just like the regular files when recovering.
        """
        return self._handle_gz

    @handle_gz.setter
    def handle_gz(self, value):
        self._handle_gz = value

    @property
    def freshstart(self):
        """
        This tells the log tailer to ignore any historic files or any knowledge
        needed for a restart, just go to the newest file and start tailing it from
        scratch (at the beginning of the file).
        """
        return self._freshstart

    @freshstart.setter
    def freshstart(self, value):
        self._freshstart = value

    def _fileglob(self):
        """
        Returns a list of files that matches the file glob information passed in.
        """
        files = glob.glob(os.path.join(self.directory,self.globstr))
        files.sort()
        return files

    def run(self):
        """
        Starts the log tailing and takes over the process in an infinite loop.
        """
        if ( self.debug ):
            print "Running."
        if ( self.singlefile ):
            self._run_singlefile()
        else:
            (filename,readcount) = ('',0)
            if ( self.recovery_file != None ):
                (filename,readcount) = self._recall()
            self._run_multifile(curfile=filename,totalread=readcount)

    def _run_singlefile(self):
        # For this run, we would need to check the file inode on each run, and when it
        # changes, reset the current read to zero.
        if ( self.debug ):
            print "Running singlefile."
        totalread = 0
        fileino = -1
        lastfileino = -1
        while ( 1 ):
            files = self._fileglob()
            if ( len(files) > 1 ):
                ValueError("Option singlefile set and more than one file returned by glob.");
            elif ( len(files) == 1 ):
                fileino = os.stat(files[0])[1];
                if ( fileino != lastfileino ):
                    lastfileino = fileino
                    totalread = 0
                totalread = self._run_file(filename=files[0],already_read=totalread);

    def _run_multifile(self,curfile='',totalread=0):
        recovery = False
        if ( self.debug ):
            print "Running multifile."
            if ( len(curfile) > 0):
                print "Running with recovery."
                recovery = True
        while ( 1 ):
            files = self._fileglob()
            skip_wait = False
            if ( len(files) ):
                if ( curfile == '' ):
                    curfile = files[-1]
                    totalread = 0
                elif ( curfile != files[-1] ):
                    idx = 0
                    for f in files:
                        if ( recovery and f == curfile or ( f[-3:] == '.gz' and f[:-3] == curfile ) ):
                            recovery = False
                            break
                        elif ( f > curfile ):
                            totalread = 0
                            break
                        else:
                            idx = idx + 1
                    curfile = files[idx]
                    if ( idx < len(files) - 1 ):
                        skip_wait = True
                totalread = self._run_file(filename=curfile,already_read=totalread,skip_wait=skip_wait)
            else:
                time.sleep(3)

    def _run_file(self,filename,already_read=0,skip_wait=False):
        fd = None
        is_gz = False
        if ( filename[-3:] == '.gz' ):
            fd = gzip.open(filename,'rb')
            is_gz = True
        else:
            fd = open(filename)
        if ( self.debug ):
            print fd
        totalread = already_read
        if ( totalread > 0 ):
            if ( is_gz ):
                fd.read(totalread)
            else:
                os.lseek(fd.fileno(),totalread,os.SEEK_SET)
        lastread = 0
        passes = 0
        while ( passes < 3 ):
            curread = ''
            if ( self.debug ):
                print "Waiting for pass: " + str(passes)
            lastread = totalread
            passes = passes + 1
            curread = '' 
            if ( is_gz ):
                curread = fd.read(self.readsize)
            else:
                curread = os.read(fd.fileno(),self.readsize)
            remainder = ''
            while ( len(curread) > 0 ):
                passes = 0
                totalread = totalread + len(curread)
                self._remember(filename,totalread)
                lines = curread.split("\n")
                if ( len(remainder) ):
                    lines[0] = remainder + lines[0]
                    remainder = ''
                linecount = len(lines)
                for i in range(linecount):
                    line = lines[i]
                    if ( i < linecount - 1 ):
                        self.process(line);
                    elif ( len(line) > 0 ):
                        remainder = line
                if ( is_gz ):
                    curread = fd.read(self.readsize)
                else:
                    curread = os.read(fd.fileno(),self.readsize) 
            if ( not skip_wait ):
                time.sleep(1) 
        if ( self.debug ):
            print "Finishing file " + filename + " with read of: " + str(totalread)
        return totalread

    def _recall(self):
        filename = ''
        readamount = 0
        if ( self.recovery_file != None ):
            if ( os.path.isfile(self.recovery_file) ):
                fh = open(self.recovery_file,'r')
                for line in fh:
                    items = line.partition(':')
                    if ( len(items[2]) ):
                        filename = items[0]
                        readamount = int(items[2])
                        break
                    break
        return ( filename , readamount )

    def _remember(self,filename,readcount):
        if ( self.recovery_file != None ):
            if ( self.debug ):
                print "Filling " + self.recovery_file
            fh = open(self.recovery_file,'w')
            mod_filename = filename
            if ( mod_filename[-3:] == '.gz' ):
                mod_filename = mod_filename[:-3]
            fh.write("{0}:{1}\n".format(mod_filename,readcount))

    def process(self,line):
        """
        This is a subroutine that may be overridden in subclasses to change how this class deals
        with a line in the log file.
        """
        print line

def default_arg_parser():
    """
    Creates an argparse ArgumentParser for parsing the command line when this utility is run as the
    main script.
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '--glob','-g',
        type=str,
        required="True",
        dest="globstr",
        help="A file glob to help find files that need to be tailed.")
    arg_parser.add_argument(
        '--directory','-d',
        type=str,
        required="True",
        dest="directory",
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
    return arg_parser

if __name__ == '__main__':
    import logtail
    import os

    arg_parser = logtail.default_arg_parser()
    options = arg_parser.parse_args()

    if options.debug == True :
        print options

    if os.path.isdir(options.directory) == True :
        lt = logtail.logtail(**(options.__dict__))
        lt.run()
