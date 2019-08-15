import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fourutils",
    version="0.0.3",
    author="Oscar Rainford",
    author_email="oscar@fourbytes.me",
    description="A compilation of utilities that I use for a number of personal projects.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fourbytes/fourutils",
    packages=setuptools.find_packages(),
    install_requires=[
        "sentry_sdk",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "webnotifications": ["pillow>=5", "pyopenssl"],
        "flask": ["flask>=1.0.0", "redis"],
        "sqlalchemy": ["sqlalchemy", "msgpack"],
        "ldap": ["ldap3"]
    }
)