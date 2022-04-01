Changelog
=========

1.3.0 (2022-04-01)
------------------

- Corrected UnicodeEncodeError.
- Removed prefix from filename
- Sort filenames naturally
- Used filename as title if no metadata
- Added script to add metadata (nothing done for now)
  [sgeulette]

1.2.5 (2020-10-07)
------------------

- Test portal type more generically.
  [sgeulette]

1.2.4 (2017-05-30)
------------------

- Set internal_reference_no if not set.
  [sgeulette]
- Added dmsmainfile portal type parameter at creation.
  [sgeulette]

1.2.3 (2016-04-15)
------------------

- Removed useless message.
  [sgeulette]

1.2.2 (2014-11-28)
------------------

- Removed a fake attribute present in the dict passed to createContentInContainer.
  [sgeulette]


1.2.1 (2014-11-27)
------------------

- Return created objects
  [sgeulette]


1.2 (2014-10-24)
----------------

- Added specific role and permission to call batchimport view
  [sgeulette]


1.1 (2014-03-24)
----------------

- Remove useless parameter
  [sgeulette]
- Don't force title
  [sgeulette]
- Skip useless directories
  [sgeulette]
- Apply default_value only if necessary
  [sgeulette]
- Pep8 corrections
  [sgeulette]

1.0 (2014-03-20)
----------------
- Improvements
  [Frédéric Péters]
- Use adopt_user to create document and main file
  [sgeulette]
- add a new @@fileimport endpoint
  [cedricmessiant]
- Added configlet
  [Frédéric Péters]
- Some improvements
  [sgeulette]
- Read and import of files
  [Frédéric Péters, David Convent]
- Package created using templer
  [cedricmessiant]
