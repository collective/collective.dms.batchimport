.. contents::

This package can read OS directories to find files to import. A metadata file can be
associated to each file.

It creates for each file a dms item containing the file as a dmsmainfile.

Introduction
============

This package provides a configuration view, where you can define:

* a path to a directory to process, called the root directory
* a path to a directory, where to move processed files
* a table where filename prefixes can be associated to portal types

The root directory can contain a directory structure that will be followed to place
in imported dms content.
This directory structure must already exist in Plone.

Each file can be joined to a metadata file in json format (A directory like
containing attributes).

Example files structure:

* "folder 1" / "file1.pdf"
* "folder 1" / "file1.pdf.metadata"
* "folder 1" / "folder2" / "file2.pdf"


Tests
=====

This add-on is tested using Github action. The current status of the add-on is :

.. image:: https://github.com/collective/collective.dms.batchimport/actions/workflows/main.yml/badge.svg
    :target: https://github.com/collective/collective.dms.batchimport/actions/workflows/main.yml
.. image:: https://coveralls.io/repos/github/collective/collective.dms.batchimport/badge.svg
    :target: https://coveralls.io/github/collective/collective.dms.batchimport
