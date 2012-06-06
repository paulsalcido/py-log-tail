import glob
import os
import time

class logtail(object):
    """
    This class can be used to tail a file and do something when new lines appear
    in it for logging.
    """
    def __init__(self,globstr,directory,debug,singlefile,readsize=10000):
        self._glob = globstr
        self._directory = directory
        self._singlefile = singlefile
        self._debug = debug
        self._handle_gz = True
        self._freshstart = False
        self._data_directory = None
        self._readsize = readsize

    @property
    def readsize(self):
        """
        This determines how many bytes are read from a file at a time.
        """
        return self._readsize

    @readsize.setter
    def _set_readsize(self,value):
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
    def _set_globstr(self, value):
        self._glob = value

    @property
    def directory(self):
        """
        This contains the directory where we will search for ordered files matching the
        glob in globstr.
        """
        return self._directory

    @directory.setter
    def _set_directory(self, value):
        self._directory = value 

    @property
    def singlefile(self):
        """
        If the globstr results in an absolute match, then this property should be set.
        This would be optimal for files like sys.log, where only one file rotates, but
        the current file only has one name.
        """
        return self._singlefile

    @singlefile.setter
    def _set_singlefile(self, value):
        self._singlefile = value

    @property
    def debug(self):
        """Set for debug output."""
        return self._debug

    @debug.setter
    def _set_debug(self,value):
        self._debug = value

    @property
    def handle_gz(self):
        """
        When apache2 rotates its files, it often gzips them.  This allows the tailer
        to treat gzip files just like the regular files when recovering.
        """
        return self._handle_gz

    @handle_gz.setter
    def _set_handle_gz(self, value):
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
    def _set_freshstart(self, value):
        self._freshstart = value

    @property
    def data_directory(self):
        """
        This contains information about where this class will keep information about
        which files it has already handled.
        """
        return self._data_directory

    @data_directory.setter
    def _set_data_directory(self, value):
        self._data_directory = value


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
        files = self._fileglob()
        if ( self.singlefile ):
            self._run_singlefile()

    def _run_singlefile(self):
        # For this run, we would need to check the file inode on each run, and when it
        # changes, reset the current read to zero.
        totalread = 0
        fileino = -1
        lastfileino = -1
        while ( 1 ):
            files = self._fileglob()
            if ( len(files) > 1 ):
                ValueError("Option singlefile set and more than one file returned by glob.");
            fileino = os.stat(files[0])[1];
            if ( fileino != lastfileino ):
                lastfileino = fileino
                totalread = 0
            totalread = totalread + self._run_file(filename=files[0],already_read=totalread);

    def _run_file(self,filename,already_read=0):
        fd = open(filename)
        print fd
        totalread = already_read
        if ( totalread > 0 ):
            os.lseek(fd.fileno(),totalread,os.SEEK_SET)
        lastread = 0
        passes = 0
        while ( passes < 3 ):
            curread = ''
            if ( self.debug ):
                print "Waiting for pass: " + str(passes)
            lastread = totalread
            passes = passes + 1
            curread = os.read(fd.fileno(),self.readsize)
            remainder = ''
            while ( len(curread) > 0 ):
                passes = 0
                totalread = totalread + len(curread)
                lines = curread.split("\n")
                if ( len(remainder) ):
                    lines[0] = remainder + lines[0]
                    remainder = ''
                linecount = len(lines)
                for i in range(linecount):
                    line = lines[i]
                    if ( i < linecount - 1 ):
                        print line
                    elif ( len(line) > 0 ):
                        remainder = line
                curread = os.read(fd.fileno(),self.readsize) 
            time.sleep(3) 
        if ( self.debug ):
            print "Finishing file " + filename + " with read of: " + str(totalread)
        return totalread
