#!/usr/bin/env python


from setuptools import setup, find_packages

# define distribution
setup(
    name = "matter",
    version = "0.8",
    packages = find_packages("python", exclude=['tests', 'notebooks']),
    package_dir = {'': "python"},
    test_suite = 'tests',
    install_requires = [
        'numpy',
        'astropy',
        # 'tomopy',
    ],
    dependency_links = [
    ],
    author = "iVenus team",
    description = "Neutron imaging data analysis at ORNL",
    license = 'BSD',
    keywords = "neutron imaging",
    url = "https://github.com/ornlneutronimaging/iVenus",
    # download_url = 'http://dev.danse.us/packages/',
)

# End of file
