*** Settings ***
Documentation  @@fileimport: one uploaded file becomes a document (portal type, location and owner given in the form).
Resource  dms_batchimport.robot
Test Setup  Open the browser and create the import directories
Test Teardown  Close the browser and remove the import directories


*** Test Cases ***
Import a file into a folder
    [Documentation]  The owner field is given as main file type on Plone 4 (MIGRATION.md Known issues)
    [Tags]  plone4-bug
    Log in as manager
    Import a file  letter.pdf  dmsincomingmail  incoming  manager
    The page is not an error
    The document is created  incoming/letter  letter

The file to import is required
    Log in as manager
    Open the file import form
    Fill the text field  portal_type  dmsincomingmail
    Click the form button  import
    The field error contains  file  Required input is missing.

A batch importer can't import a file
    Log in as importer
    Open the file import form
    The access is refused
