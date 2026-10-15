from setuptools import setup

version = "2.0.0.dev0"

long_description = (
    open("README.rst").read() + "\n" + "Contributors\n"
    "============\n"
    + "\n"
    + open("CONTRIBUTORS.rst").read()
    + "\n"
    + open("CHANGES.rst").read()
    + "\n"
)

setup(
    name="collective.dms.batchimport",
    version=version,
    description="Batch import of files into the Documents Management System",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="Python Zope Plone",
    author="Cedric Messiant",
    author_email="dev@imio.be",
    project_urls={
        "PyPI": "https://pypi.python.org/project/collective.dms.batchimport",
        "Source": "https://github.com/collective/collective.dms.batchimport",
    },
    license="gpl",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "collective.dms.mailcontent",
        "collective.z3cform.datagridfield",
        "imio.helpers",
        "imio.pyutils",
        "natsort",
        "plone.api",
        "plone.app.registry",
        "plone.autoform",
        "plone.base",
        "plone.dexterity",
        "plone.i18n",
        "plone.namedfile",
        "plone.protect",
        "plone.registry",
        "Products.CMFCore",
        "z3c.form",
        "Zope",
    ],
    extras_require={
        "test": [
            "collective.dms.basecontent",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.testing",
            "robotsuite",
        ],
    },
    entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      [console_scripts]
      batchimport_add_metadata = collective.dms.batchimport.script:add_metadata
      """,
)
