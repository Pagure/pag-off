#!/usr/bin/env python

"""
Setup script
"""

import os
import re

from setuptools import setup


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    with open(requirements_file) as f:
        return [
            line.rstrip().split('#')[0]
            for line in f.readlines()
            if not line.startswith('#')
        ]


setup(
    name='pag-off',
    description='Small utility to interact with pagure\'s tickets and'
        ' pull-requests offline.',
    version='0.1',
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv2+',
    download_url='https://pagure.io/releases/pag-off',
    url='https://pagure.io/pag-off/',
    packages=['pag_off'],
    install_requires=get_requirements(),
    entry_points="""
    [moksha.consumer]
    pag-off = pag_off.app:main
    """,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Bug Tracking',
    ]
)
