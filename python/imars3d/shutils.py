

def exec_withlog(cmd, logfile):
    import subprocess as sp, shlex
    args = shlex.split(cmd)
    outstream = open(logfile, 'wt')
    outstream.write('%s\n\n' % cmd)
    print("* Running %s" % cmd)
    if sp.call(args, stdout=outstream, stderr=outstream, shell=False):
        raise RuntimeError("%s failed. See log file %s" % (cmd, logfile))
    print(" - Done.")
    return
