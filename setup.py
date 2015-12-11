#!/usr/bin/env python

from setuptools import setup, find_packages

# define distribution
setup(
    name = "ivenus",
    version = open('VERSION').read().strip(),
    packages = find_packages(),
    author = "iVenus team",
    description = "Neutron imaging data analysis at ORNL",
    license = 'BSD',
    keywords = ["neutron imaging"],
    url = 'http://ivenus.readthedocs.org',
    download_url = 'https://github.com/ornlneutronimaging/ivenus.git',
    classifiers = [
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: C']
)

# End of file
