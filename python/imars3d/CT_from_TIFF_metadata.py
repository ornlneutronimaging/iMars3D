"""
CT2 data object
This one uses metadata in image TIFF files.

GroupID - Unique ID for a radiograph or CT. It equals to the RunNo of the first run in the group.
GroupSize - Number of expected images in a radiograph or CT 
RunNo - Incrementing number for each image in a radiograph or CT 
FrameIndex - The frame index for each each position for a radiograph or CT (starting at 1). This will be reset to 1 for each new CT position.

So for a CT scan:
  GroupSize = number of frames at each position * (int((end-start)/step) + 1)

where end, start and step are the CT motor positions, and the number of frames is the number of images taken at each position.

For auto-reconstruction, the logic described below should hold:
  If RunNo = GroupID + GroupSize - 1, start data reduction

"""


import os, glob, warnings
import numpy as np, tifffile
import imars3d as i3
import progressbar
from . import decorators as dec
from imars3d import configuration
pb_config = configuration['progress_bar']



def autoreduce(
        ct_file_path, 
        local_disk_partition='/SNSlocal2', outdir=None, 
        clean_intermediate_files='on_the_fly',  # on_the_fly, archive, False
        parallel_nodes=20, 
        crop_window=None, tilt=None
):
    meta = readTIFMetadata(ct_file_path)
    RunNo = int(meta['RunNo'])
    GroupID = int(meta['GroupID'])
    GroupSize = int(meta['GroupSize'])
    fn = os.path.basename(ct_file_path)
    if RunNo < GroupID + GroupSize - 1:
        print("%s: Not the last file of the CT. skip" % fn)
        return
    if RunNo < GroupID + GroupSize - 1:
        raise RuntimeError("Corrupted file? See %s" % ct_file_path)
    ipts_dir = getIPTSdir(ct_file_path)
    autoreduce_dir = os.path.join(ipts_dir, 'shared', 'autoreduce')
    if not os.path.exists(autoreduce_dir):
        os.makedirs(autoreduce_dir)
    workdir = os.path.join(local_disk_partition, '__autoreduce.CT-group-%s' % GroupID)
    if os.path.exists(workdir):
        if os.path.islink(workdir):
            os.unlink(workdir)
        else:
            import shutil
            shutil.rmtree(workdir)
    if outdir is None:
        fn2 = meta.get('FileNameStr', fn)
        tokens = ['CT-group', str(GroupID), fn2]
        sample_desc = meta.get('SampleDescStr')
        if sample_desc:
            sample_desc = ''.join([i for i in sample_desc if ord(i) < 128 and ord(i)>31])
            tokens.append(sample_desc)
        outdirname = '-'.join(tokens)
        outdir = os.path.join(autoreduce_dir, outdirname) 
    ct = CT(
        ct_file_path,
        workdir=workdir, outdir=outdir, 
        parallel_preprocessing=True,
        parallel_nodes=parallel_nodes,
        clean_intermediate_files = clean_intermediate_files,
        vertical_range=None,
    )
    ct.preprocess()
    ct.recon(crop_window=crop_window, tilt=tilt)
    return
    


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
            workdir='work', outdir='out', 
            parallel_preprocessing=True, parallel_nodes=None,
            clean_intermediate_files=None,
            vertical_range=None,
    ):
        import logging; self.logger = logging.getLogger("CT_from_TIFF_metadata")
        self.ct_file_path = ct_file_path
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
        ct_series = io.ImageFileSeries(ct_pattern, identifiers = angles, name = "CT", decimal_mark_replacement='.')
        # open beam
        ob_files = self._find_OB_DF_files('Open Beam', 'ob')
        obs = io.imageCollection(files=ob_files, name="Open Beam")
        # dark field
        df_files = self._find_OB_DF_files('Dark field', 'df', fail_on_not_found=False)
        if df_files is not None:
            dfs = io.imageCollection(files=df_files, name="Dark Field")
        else:
            dfs = None
        return ct_series, angles, dfs, obs


    def _find_OB_DF_files(self, type, subdir, fail_on_not_found=True):
        f1 = self.ct_file_path
        ipts_dir = getIPTSdir(f1)
        # ob subdir
        ob_dir = os.path.join(ipts_dir, 'raw', subdir)
        # find all files and their mtimes
        candidates = findFiles(ob_dir, '*.tiff')
        out = []; mtimes = []; exposures = {}
        day = 24*3600.
        # only keep files that are not too old. keep records of exposure and mod time
        for p in candidates:
            e = os.path.basename(p)
            mt = os.path.getmtime(p)
            # OB file mtime should be not too early
            if mt < self.earliest_ct_mtime - day:
                self.logger.debug("%s file %s is too old" % (type, e))
                continue
            md = readTIFMetadata(p)
            if 'ExposureTime' not in md:
                print("missing ExposureTime in %s" % p)
                continue
            et = float(md['ExposureTime'])
            if not np.isclose(et, self.exposure_time):
                self.logger.debug("%s file %s was exposed %s seconds, but CT was exposed %s seconds" % (
                    type, p, et, self.exposure_time))
                if et < self.exposure_time*.8 or et > self.exposure_time*1.2:
                    # difference too large, skip
                    continue
            self.logger.info("Found %s: %s" % (type, p))
            out.append(p); mtimes.append(mt); exposures[p] = et
            continue
        # these files are newer than {earliest CT mtime}-1day.
        # first see if there are files older than {earliest CT mtime}
        before_CT = [c for c, mt in zip(out, mtimes) if mt < self.earliest_ct_mtime]
        if len(before_CT) > 0:
            out = before_CT
        else:
            # if there is no files before CT is taken, try to see if there are files
            # within 24 hours after the last CT
            after_CT = [c for c, mt in zip(out, mtimes) if mt < self.latest_ct_mtime + day]
            if len(after_CT) > 0:
                out = after_CT
            else:
                # all files are newer than {last-CT-mtime}+1day
                msg = 'No files within one day of CT measurement. will use %s files after one day of CT measurement' % type
                warnings.warn(msg)
                out = [x for _, x in sorted(zip(mtimes, out))]
                out = out[:10]
        # nothing good. bail out
        if len(out) == 0:
            msg = "There is no %s files either within one day of CT measurement, or after CT measurement" % type
            if fail_on_not_found: raise RuntimeError(msg)
            warnings.warn(msg)
            return
        if len(out) < 5:
            warnings.warn("Too few %s files" % type)
        # if there are enough files with good exposure, just return it
        good = [f for f in out if np.isclose(exposures[f], self.exposure_time)]
        if len(good) >= 5: return good
        # calculate distance of exposure time and sort by distance and pick the first 10
        distances = [abs(exposures[f]-self.exposure_time) for f in out]
        out = [x for _, x in sorted(zip(distances, out))]
        out = out[:10]
        # go thru the file list, for each file that has different exposure, create a new file scaled
        scaled_dir = os.path.join(self.workdir, '%s-scaled-by-exposure' % type)
        if not os.path.exists(scaled_dir): os.makedirs(scaled_dir)
        for i, f in enumerate(out):
            et = exposures[f]
            if np.isclose(et, self.exposure_time): continue
            with tifffile.TiffFile(f) as tif:
                page = tif[0]
                data = page.asarray() * (1.*self.exposure_time/et)
                # save a new file
                newpath = os.path.join(scaled_dir, '%s_%s' % (i, os.path.basename(f)))
                tifffile.imsave(newpath, data)
                out[i] = newpath
            continue
        return out

    ct_filename_template = 'at_%s.tiff'
    def _getCTfiles(self):
        f1 = self.ct_file_path
        metadata = readTIFMetadata(f1)
        groupID = int(metadata['GroupID'])
        # assume CT files are all in the same directory
        dir = os.path.dirname(f1)
        files = []; angles = []; mtimes = []; exposure_times = []
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
            exposure_times.append(float(meta1['ExposureTime']))
            mtimes.append(os.path.getmtime(p))
            continue
        # check and save exposure times. needed for checking OB and DF
        et = np.average(exposure_times)
        assert np.allclose(exposure_times, et)
        self.exposure_time = et
        # remember these. OB and DF sniffing needs this
        self.earliest_ct_mtime = np.min(mtimes) 
        self.latest_ct_mtime = np.max(mtimes)
        frame_size = int(metadata['FrameSize'])
        # temp directory to hold CT
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
            self.logger.info("Averaging frames from %s" % (map(os.path.basename, files1),))
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
            self.logger.info("Adding %s. angle=%s"  % (newpath, ave_angle))
            continue
        return output_files, np.array(output_angles)

    
def findFiles(dir, pattern):
    import fnmatch
    import os
    matches = []
    for root, dirnames, filenames in os.walk(dir):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


def getIPTSdir(f1):
    # get the IPTS folder path
    tokens = f1.split('/')
    p = ''
    for token in tokens:
        p += token + '/'
        if token.startswith('IPTS'): break
    return p

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
