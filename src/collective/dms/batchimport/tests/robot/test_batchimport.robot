*** Settings ***
Documentation  @@batchimport: the files of the import directory become documents (code-title file names,
...            .metadata json files, sub-directories as folders), the imported files are moved to the processed
...            directory.
Resource  dms_batchimport.robot
Test Setup  Open the browser and create the import directories
Test Teardown  Close the browser and remove the import directories


*** Test Cases ***
Import the files of the import directory
    Create a scanned file  123-Letter.pdf
    Create a scanned file  123-Scan.pdf
    Create a metadata file  123-Scan.pdf.metadata  {"title": "Invoice"}
    Create a scanned file  incoming/123-Complaint.pdf
    Create a scanned file  .hidden.pdf
    Set up the incoming mail import
    Run the batch import
    The batch import result is  3  0
    The document is created  letter  Letter
    The document is created  invoice  Invoice
    The document is created  incoming/complaint  Complaint
    The import file is moved  123-Letter.pdf
    The import file is moved  123-Scan.pdf
    The import file is moved  123-Scan.pdf.metadata
    The import file is moved  incoming/123-Complaint.pdf
    The import file is not moved  .hidden.pdf

Files that can't be imported stay in the import directory
    Create a scanned file  999-Unknown code.pdf
    Create a scanned file  archives/123-No folder.pdf
    Set up the incoming mail import
    Run the batch import
    The batch import result is  0  2
    The import file is not moved  999-Unknown code.pdf
    The import file is not moved  archives/123-No folder.pdf

A batch importer runs the batch import
    Set up the incoming mail import
    Create a scanned file  123-Letter.pdf
    Log in as importer
    Run the batch import
    The batch import result is  1  0
    The document is created  letter  Letter

A member can't run the batch import
    Log in as member
    Run the batch import
    The access is refused

The file keys of a metadata file are fields of the main file
    [Documentation]  RuntimeError on Plone 4 (MIGRATION.md Known issues)
    [Tags]  plone4-bug
    Create a scanned file  123-Scan.pdf
    Create a metadata file  123-Scan.pdf.metadata  {"title": "Invoice", "file_title": "Original scan"}
    Set up the incoming mail import
    Run the batch import
    The batch import result is  1  0
    Go to  ${PLONE_URL}/invoice/original-scan
    The page title contains  Original scan
