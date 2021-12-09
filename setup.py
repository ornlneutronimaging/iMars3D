#!/usr/bin/env python


from setuptools import setup, find_packages

# define distribution
setup(
    name="imars3d",
    version="0.1.3",
    packages=find_packages("python", exclude=['tests', 'notebooks']),
    package_dir={'': "python"},
    test_suite='tests',
    install_requires=['numpy',
                      'astropy',
                      # 'tomopy',
                     ],
    dependency_links=[],
    author="iMars3D team",
    description="Neutron imaging data analysis at ORNL",
    license='BSD',
    keywords="neutron imaging",
    url="https://github.com/ornlneutronimaging/iMars3D",
    # download_url = '',
)

# End of file
