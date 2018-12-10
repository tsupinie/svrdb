
from setuptools import setup, find_packages
import svrdb._svrdb_version as version

setup(
    name = 'svrdb',
    version = version.get_version(),
    author = 'Tim Supinie',
    author_email = 'tsupinie@gmail.com',
    description = 'SPC severe weather database tools',
    license = 'GPLv3',
    keywords = 'meteorology spc reports',
    url = 'https://github.com/tsupinie/svrdb',
    packages = ['svrdb'],
    package_data = {'svrdb':['data/*']},
    include_package_data = True,
)
