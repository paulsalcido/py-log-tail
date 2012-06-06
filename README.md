py-log-tail
===========

A log tailing solution in python, with a process event model, handling log rotations in multiple ways

I'm initially writing this as a way to learn how to code in python while also doing something useful.  Where I work, we originally tried to use logstash, but memory and speed issues persisted.  I recoded major portions of it in perl, but this I want to be a more flexible log tailer that will work no matter what the files are (well kind of).

As we all know, tail -f handles multiple files, but what this is really about is handling file rotation in a really good way.  I also want to code in catch up and what not, because we've had issues with the process stopping and restarting, etc.  I'll be adding in a storage method as I learn about python to handle remembering which files I've done and to refind my current location and start tailing again.
