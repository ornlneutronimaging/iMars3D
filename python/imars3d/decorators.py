import os, imars3d

__timeit__logfile = "log.timeit"
__timeit__logstream = open(__timeit__logfile, 'wt')
def timeit(method):

    def timed(*args, **kw):
        import time                                                
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        __timeit__logstream.write(
            '%r (%r, %r) %2.2f sec\n' % (method.__name__, args, kw, te-ts)
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
    import logging; logger = logging.getLogger("mpi")
    tmpdir="_mpi_tmp/%s" % (f.__name__,)
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    def _(*args, **kwds):
        # nodes kwd
        nodes = kwds.pop('nodes') if 'nodes' in kwds else None
        #
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
        # number of cpus
        if not nodes:
            import psutil
            nodes = psutil.cpu_count() - 1
        nodes = max(nodes, 1)
        nodes = min(nodes, imars3d.configuration['parallelization']['max_nodes'])
        # shell cmd
        cmd = 'mpirun -np %(nodes)s python %(pyfile)s' % locals()
        logger.info("* running %s" % cmd)
        logger.info("  - args: %s" % (args,))
        logger.info("  - kwds:")
        for k,v in kwds.items():
            logger.info("    - %s: %s" % (k,v))
            continue
        from .shutils import exec_redirect_to_stdout
        exec_redirect_to_stdout(cmd)
        logger.info("done.")
        return
    return _
