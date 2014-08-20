from setuptools import setup, find_packages

setup(
    name="vxfld",
    version="1.0",
    packages=find_packages(),
    scripts=[
        'bin/vxsnd',
        'bin/vxrd',
    ],

    install_requires=[
        'python-daemon',
        'dpkt',
        'pyip',
        'docopt',
    ],

    # metadata for upload to PyPI
    author="Cumulus Networks/Metacloud Engineering",
    author_email="info@cumulusnetworks.com",
    description="VXLAN Flooding Service",
    license="GPLv2",
)
