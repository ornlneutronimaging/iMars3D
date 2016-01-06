#!/usr/bin/env python


from setuptools import setup, find_packages

# define distribution
setup(
    name = "ivenus",
    version = "0.1",
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
    # download_url = '',
)

# End of file
