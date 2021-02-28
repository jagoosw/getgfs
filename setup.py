from distutils.core import setup

setup(
    # Application name:
    name="getgfs",

    # Version number (initial):
    version="0.0.0",

    # Application author details:
    author="Jago Strong-Wright",
    author_email="jagoosw@protonmail.com",

    # Packages
    packages=["getgfs"],

    # Details
    url="https://github.com/jagoosw/getgfs/",

    #
    license="LICENSE.txt",
    description="Extracts weather forecast variables from the NOAA GFS forecast in a pure python, no obscure dependencies way",

    long_description="""Please see the homepage as the readme wouldn't render here""",

    # Dependent packages (distributions)
    install_requires=[
        "scipy",
        "requests",
        "fuzzywuzzy",
        "numpy",
        "python_dateutil",
        "regex"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: Markdown"
    ],
)