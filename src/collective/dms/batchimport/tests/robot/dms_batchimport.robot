*** Settings ***
Documentation  collective.dms.batchimport keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Fixture (testing.py, ACCEPTANCE): default profile, a categories config, user manager (Manager: the
...            control panel and @@fileimport need Manage portal), user importer (Batch importer and Contributor
...            roles), user member, folder /incoming. Import and processed directories: temporary directories of
...            each test.
Resource  ui_plone${PLONE_MAJOR}.robot
Library  OperatingSystem


*** Variables ***
${MANAGER}  manager
${MANAGER_PASSWORD}  Manager!12
${IMPORTER}  importer
${IMPORTER_PASSWORD}  Import!123
${MEMBER}  member
${MEMBER_PASSWORD}  Member!123


*** Keywords ***
Log in as manager
    Log in with the login form  ${MANAGER}  ${MANAGER_PASSWORD}

Log in as importer
    Log in with the login form  ${IMPORTER}  ${IMPORTER_PASSWORD}

Log in as member
    Log in with the login form  ${MEMBER}  ${MEMBER_PASSWORD}

Open the browser and create the import directories
    [Documentation]  Test setup: sets ${IMPORT_DIR} and ${PROCESSED_DIR}
    ${import_dir} =  Evaluate  tempfile.mkdtemp(prefix="import-")  modules=tempfile
    ${processed_dir} =  Evaluate  tempfile.mkdtemp(prefix="processed-")  modules=tempfile
    Set test variable  ${IMPORT_DIR}  ${import_dir}
    Set test variable  ${PROCESSED_DIR}  ${processed_dir}
    Open test browser

Close the browser and remove the import directories
    Close all browsers
    Remove directory  ${IMPORT_DIR}  recursive=${True}
    Remove directory  ${PROCESSED_DIR}  recursive=${True}

Create a scanned file
    [Documentation]  File of the import directory (path relative to it), its directories created
    [Arguments]  ${path}
    Create file  ${IMPORT_DIR}/${path}  %PDF-1.4 scan

Create a metadata file
    [Documentation]  .metadata json file of the import directory
    [Arguments]  ${path}  ${json}
    Create file  ${IMPORT_DIR}/${path}  ${json}  encoding=UTF-8

The import file is moved
    [Documentation]  From the import directory to the processed directory, same relative path
    [Arguments]  ${path}
    File should not exist  ${IMPORT_DIR}/${path}
    File should exist  ${PROCESSED_DIR}/${path}

The import file is not moved
    [Arguments]  ${path}
    File should exist  ${IMPORT_DIR}/${path}
    File should not exist  ${PROCESSED_DIR}/${path}

The page title contains
    [Documentation]  Heading of a content view or a form
    [Arguments]  ${text}
    Element should contain  css=#content h1  ${text}

Fill the text field
    [Documentation]  Text input or text area of a z3c.form page
    [Arguments]  ${field_name}  ${value}
    Input text  css=#form-widgets-${field_name}  ${value}

The text field shows
    [Arguments]  ${field_name}  ${value}
    Textfield value should be  css=#form-widgets-${field_name}  ${value}

Open the batch import settings
    [Documentation]  Batch Import configlet, from the Site Setup
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click the control panel link  Batch Import
    Location should be  ${PLONE_URL}/@@batchimport-controlpanel

Change the batch import settings
    [Documentation]  Import and processed directories, mapping of one code (first row)
    [Arguments]  ${import_dir}  ${processed_dir}  ${code}  ${portal_type}
    Open the batch import settings
    Fill the text field  fs_root_directory  ${import_dir}
    Fill the text field  processed_fs_root_directory  ${processed_dir}
    Fill the datagrid cell  code_to_type_mapping  1  code  ${code}
    Fill the datagrid cell  code_to_type_mapping  1  portal_type  ${portal_type}
    Click the form button  save
    The status message contains  Changes saved

Set up the incoming mail import
    [Documentation]  Settings of the test directories, code 123 for incoming mails (as manager)
    Log in as manager
    Change the batch import settings  ${IMPORT_DIR}  ${PROCESSED_DIR}  123  dmsincomingmail

Run the batch import
    Go to  ${PLONE_URL}/@@batchimport

The batch import result is
    [Arguments]  ${imported}  ${unprocessed}
    Page should contain  OK (${imported} imported files, ${unprocessed} unprocessed files)

The document is created
    [Documentation]  Document (by path from the site) with its main file (its view: the default view of a file
    ...              without category, iconifiedcategory's @@display-file, is an error page, see MIGRATION.md)
    [Arguments]  ${path}  ${title}
    Go to  ${PLONE_URL}/${path}
    The page title contains  ${title}
    Go to  ${PLONE_URL}/${path}/scanned-mail/view
    The page title contains  Scanned Mail

Open the file import form
    Go to  ${PLONE_URL}/@@fileimport

Import a file
    [Documentation]  @@fileimport with a new file of this name (written in the import directory)
    [Arguments]  ${filename}  ${portal_type}  ${location}  ${owner}
    Create a scanned file  ${filename}
    Open the file import form
    Choose the file  file  ${IMPORT_DIR}/${filename}
    Fill the text field  portal_type  ${portal_type}
    Fill the text field  location  ${location}
    Fill the text field  owner  ${owner}
    Click the form button  import
