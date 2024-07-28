from distutils.core import setup

setup(
    # Application name:
    name="getgfs",
    # Version number (initial):
    version="1.2.0",
    # Application author details:
    author="Jago Strong-Wright",
    author_email="jagoosw@protonmail.com",
    # Packages
    packages=["getgfs"],
    # Details
    url="https://getgfs.readthedocs.io/",
    #
    license="LICENSE.txt",
    description="getgfs extracts weather forecast variables from the NOAA GFS forecast",
    # Dependent packages (distributions)
    install_requires=[
        "scipy",
        "requests",
        "fuzzywuzzy",
        "numpy",
        "python_dateutil",
        "regex",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: Markdown",
    ],
)
