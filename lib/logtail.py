import glob
import os
import time

class logtail(object):
    """
    This class can be used to tail a file and do something when new lines appear
    in it for logging.
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
        The directory where we will search for matching files.
        """
        return self._directory

    @directory.setter
    def _set_directory(self, value):
        self._directory = value 

    @property
    def recovery_file(self):
        """
        The file that will remember the last file read for multifile read recovery.
        """
        return self._recovery_file

    @directory.setter
    def _set_recovery_file(self, value):
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
            fileino = os.stat(files[0])[1];
            if ( fileino != lastfileino ):
                lastfileino = fileino
                totalread = 0
            totalread = totalread + self._run_file(filename=files[0],already_read=totalread);

    def _run_multifile(self,curfile='',totalread=0):
        if ( self.debug ):
            print "Running multifile."
        while ( 1 ):
            files = self._fileglob()
            if ( len(files) ):
                if ( curfile == '' ):
                    curfile = files[-1]
                    totalread = 0
                elif ( curfile != files[-1] ):
                    idx = 0
                    for f in files:
                        if ( f > curfile ):
                            break
                        else:
                            idx = idx + 1
                    curfile = files[idx]
                    totalread = 0
                totalread = totalread + self._run_file(filename=curfile,already_read=totalread)
            else:
                time.sleep(3)

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
            while ( len(curread) > 0 ):
                passes = 0
                totalread = totalread + len(curread)
                self._remember(filename,totalread)
                lines = curread.split("\n")
                for line in lines:
                    # This is where process will go.
                    self.process(line)
                curread = os.read(fd.fileno(),self.readsize) 
            time.sleep(3) 
        if ( self.debug ):
            print "Finishing file " + filename + " with read of: " + str(totalread)
        return totalread

    def _recall(self):
        filename = ''
        readamount = 0
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
        fh = open(self.recovery_file,'w')
        fh.write("{0}:{1}\n".format(filename,readcount))

    def process(self,line):
        print line

