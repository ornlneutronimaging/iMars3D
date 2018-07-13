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
        ct_files, angles = self._getCTfiles()
        return


    def _getCTfiles(self):
        f1 = self.ct_file_path
        metadata = readTIFMetadata(f1)
        groupID = int(metadata['GroupID'])
        # assume CT files are all in the same directory
        dir = os.path.dirname(f1)
        files = []; angles = []
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
            continue
        frame_size = int(metadata['FrameSize'])
        # temp directory to hold CT
        if frame_size != 1:
            ct_dir = os.path.join(self.workdir, 'CT_frame_averaged')
            if not os.path.exists(ct_dir): os.makedirs(ct_dir)
        # 
        angle_file_list = sorted(zip(angles, files))
        output_files = []; output_angles = []
        for index, (angle, path) in enumerate(angle_file_list):
            if frame_size == 1:
                output_files.append(path)
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
            path = os.path.join(ct_dir, 'at_%s.tiff' % ave_angle)
            tifffile.imsave(path, data)
            output_files.append(path)
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
