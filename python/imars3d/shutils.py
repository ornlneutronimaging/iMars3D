
def exec_redirect_to_stdout(cmd, shell=False):
    "execute a command in a subproces and redirect outputs (including errors) to sys.stdout"
    import subprocess as sp, shlex, sys
    args = shlex.split(cmd)
    # sp.check_call(args, shell=shell)
    # manually pipe the output from the subprocess to sys.stdout so that
    # jupyter gets it inside the web page instead of the stdout of the terminal
    # from which jupyter is launched
    p = sp.Popen(args, shell=shell, stdout=sp.PIPE, stderr=sp.STDOUT)

    # FIXME TODO : Popen API changes from python 2.7 to 3.6.  Require further work on this
    # FIXME: skip output temporarily
    # for c in iter(lambda: p.stdout.read(1), ''):
    #     if isinstance(c, str):
    #         # stdout.write requir string
    #         sys.stdout.write(c)

    p.communicate()
    r = p.poll()
    if r:
        raise RuntimeError("Cmd %r failed" % cmd)
    return


def exec_withlog(cmd, logfile):
    import subprocess as sp, shlex
    args = shlex.split(cmd)
    outstream = open(logfile, 'wt')
    outstream.write('%s\n\n' % cmd)
    print("* Running %s" % cmd)
    if sp.call(args, stdout=outstream, stderr=outstream, shell=False):
        outstream.close()
        log = open(logfile).read()
        raise RuntimeError("%s failed. See log file %s\n%s\n" % (cmd, logfile, log))
    print(" - Done.")
    return
