# CT2 data object
# This one uses metadata in image TIFF files.

import os, glob
import numpy as np, tifffile
import imars3d as i3
import progressbar
from . import decorators as dec
from imars3d import configuration
pb_config = configuration['progress_bar']


from .CTProcessor import CTProcessor
class CT(CTProcessor):

    __doc__ = """CT reconstruction engine

This is the second CTProcessor class implemented.
It uses metadata in TIFF to find the CT/OB/DF files.

>>> ct = CT(...)
>>> ct.preprocess()
>>> ct.recon()
""" + CTProcessor.__processor_doc__

    def __init__(
            self, ct_file_path,
            skip_df=False,
            workdir='work', outdir='out', 
            parallel_preprocessing=True, parallel_nodes=None,
            clean_intermediate_files=None,
            vertical_range=None,
    ):
        import logging; self.logger = logging.getLogger("CT_from_TIFF_metadata")
        self.ct_file_path = ct_file_path
        self.skip_df = skip_df
        # workdir
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        self.workdir = workdir
        ct_series, angles, dfs, obs = self.sniff()
        CTProcessor.__init__(
            self,
            ct_series, angles, dfs, obs,
            workdir=workdir, outdir=outdir, 
            parallel_preprocessing=parallel_preprocessing, parallel_nodes=parallel_nodes,
            clean_intermediate_files=clean_intermediate_files,
            vertical_range=vertical_range,
            )
        return


    def sniff(self):
        from . import io
        ct_files, angles = self._getCTfiles()
        ct_pattern = os.path.join(self.ct_dir, self.ct_filename_template)
        ct_series = io.ImageFileSeries(ct_pattern, identifiers = angles, name = "CT")
        # open beam
        ob_files = self._find_OB_DF_files('Open Beam', 'ob')
        obs = io.imageCollection(files=ob_files, name="Open Beam")
        # dark field
        if not self.skip_df:
            df_files = self._find_OB_DF_files('Dark field', 'df')
            dfs = io.imageCollection(files=df_files, name="Dark Field")
        else:
            dfs = None
        return ct_series, angles, dfs, obs


    def _find_OB_DF_files(self, type, subdir):
        f1 = self.ct_file_path
        # get the IPTS folder path
        tokens = f1.split('/')
        p = ''
        for token in tokens:
            p += token + '/'
            if token.startswith('IPTS'): break
        ipts_dir = p
        # ob subdir
        ob_dir = os.path.join(ipts_dir, 'raw', subdir)
        # files and their mtimes
        entries = os.listdir(ob_dir)
        out = []
        day = 24*3600.
        for e in entries:
            p = os.path.join(ob_dir, e)
            mt = os.path.getmtime(p)
            # OB file mtime should be not too early
            if mt > self.earliest_ct_mtime - day:
                out.append(p)
            continue
        if len(out) == 0:
            raise RuntimeError("There is no %s files within one day of CT measurement" % type)
        if len(out) < 5:
            import warnings
            warnings.warn("Too few %s files" % type)
        return out

    ct_filename_template = 'at_%s.tiff'
    def _getCTfiles(self):
        f1 = self.ct_file_path
        metadata = readTIFMetadata(f1)
        groupID = int(metadata['GroupID'])
        # assume CT files are all in the same directory
        dir = os.path.dirname(f1)
        files = []; angles = []; mtimes = []
        for entry in os.listdir(dir):
            p = os.path.join(dir, entry)
            if os.path.isdir(p): continue
            try:
                meta1 = readTIFMetadata(p)
            except ValueError as e:
                if str(e) != 'not a valid TIFF file':
                    raise
                continue
            groupID1 = int(meta1['GroupID'])
            if groupID1 != groupID: continue
            files.append(p)
            angles.append(float(meta1['RotationActual']))
            mtimes.append(os.path.getmtime(f1))
            continue
        self.earliest_ct_mtime = np.min(mtimes) # remember this. OB and DF sniffing needs this
        frame_size = int(metadata['FrameSize'])
        # temp directory to hold CT
        if frame_size != 1:
            self.ct_dir = ct_dir = os.path.join(self.workdir, 'CT_frame_averaged')
            if not os.path.exists(ct_dir): os.makedirs(ct_dir)
        # 
        angle_file_list = sorted(zip(angles, files))
        output_files = []; output_angles = []
        for index, (angle, path) in enumerate(angle_file_list):
            if frame_size == 1:
                newpath = os.path.join(ct_dir, self.ct_filename_template % angle)
                os.symlink(path, newpath)
                output_files.append(newpath)
                output_angles.append(angle)
                continue
            # need average
            # skip until the last frame
            if index % frame_size != frame_size-1: continue
            # get all frames
            sublist = angle_file_list[index-(frame_size-1): index+1]
            angles1 = []; files1 = []
            for a, f in sublist:
                angles1.append(a); files1.append(f)
            # make sure all frames have the same angle
            ave_angle = np.average(angles1)
            assert np.allclose(angles1, ave_angle, atol=1e-3), "angle values incosistent: %s" % (angles1,)
            # average data of all frames
            data = 0.
            for f1 in files1:
                with tifffile.TiffFile(f1) as tif:
                    page = tif[0]
                    data += page.asarray()
                continue
            data/=frame_size
            # save a new file
            newpath = os.path.join(ct_dir, self.ct_filename_template % ave_angle)
            tifffile.imsave(newpath, data)
            # 
            output_files.append(newpath)
            output_angles.append(ave_angle)
            continue
        return output_files, output_angles


def readTIFMetadata(f1):
    metadata = dict()
    with tifffile.TiffFile(f1) as tif:
        p0 = tif[0]
        for tag in p0.tags.values():
            v = tag.value
            if not isinstance(v, basestring): continue
            tokens = v.split(':')
            if len(tokens)!=2: continue
            name, value = tokens
            metadata[name] = value
            continue
    return metadata
# End of file
