#!/usr/bin/env python
import subprocess

from setuptools import setup


def get_version():
    try:
        output = subprocess.check_output(  # nosec
            ['git', 'describe', '--tags']
        ).decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        try:
            tag, commit_num, sha = output.split('-', 3)
        except ValueError:
            pep440_version = output
        else:
            pep440_version = '%s.dev%s' % (tag, commit_num)

        return pep440_version


setup(version=get_version())
