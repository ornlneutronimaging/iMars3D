import os

__timeit__logfile = "log.timeit"
__timeit__logstream = open(__timeit__logfile, 'wt')
def timeit(method):

    def timed(*args, **kw):
        import time                                                
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print(
            '%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te-ts),
            file=__timeit__logstream
        )
        # __timeit__logstream.flush()
        return result

    return timed



def mpi_parallelize(f):
    import_statement = 'from %s import %s as method' % (
        f.__module__, f.__name__)
    py_code_template = """
import pickle
args, kwds = pickle.load(open(%(args_pkl)r, 'rb'))

""" + import_statement + """
method(*args, **kwds)
"""
    tmpdir="_mpi_tmp/%s" % (f.__name__,)
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    def _(*args, **kwds):
        import tempfile, pickle
        dir = tempfile.mkdtemp(dir=tmpdir)
        # save params
        args_pkl = os.path.join(dir, "args.pkl")
        allargs = args, kwds
        pickle.dump(allargs, open(args_pkl, 'wb'))
        # write python code
        pycode = py_code_template % locals()
        pyfile = os.path.join(dir, "run.py")
        open(pyfile, 'wt').write(pycode)
        # cpus
        nodes = kwds.get('nodes', None)
        if not nodes:
            import psutil
            nodes = psutil.cpu_count() - 1
        nodes = max(nodes, 1)
        nodes = min(nodes, 10)
        # shell cmd
        cmd = 'mpirun -np %(nodes)s python %(pyfile)s' % locals()
        print("* running %s" % cmd)
        print("  - args: %s" % (args,))
        print("  - kwds:")
        for k,v in kwds.iteritems():
            print("    - %s: %s" % (k,v))
            continue
        import subprocess as sp, shlex
        args = shlex.split(cmd)
        logfile = os.path.join(dir, 'log.run')
        print("  - logging in %s" % os.path.abspath(logfile))
        outstream = open(logfile, 'wt')
        outstream.write('%s\n\n' % cmd)
        if sp.call(args, stdout=outstream, stderr=outstream, shell=False):
            raise RuntimeError("%s failed. See log file %s" % (cmd, logfile))
        print("done.")
        return
    return _
