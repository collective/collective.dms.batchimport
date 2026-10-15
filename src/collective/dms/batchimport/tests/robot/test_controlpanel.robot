*** Settings ***
Documentation  The Batch Import control panel: import and processed directories, code to portal type mapping.
Resource  dms_batchimport.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Open the batch import control panel from the Site Setup
    Log in as manager
    Open the batch import settings
    The page title contains  Batch Import Settings

Save the batch import settings
    Log in as manager
    Change the batch import settings  /srv/import  /srv/processed  123  dmsincomingmail
    Open the batch import settings
    The text field shows  fs_root_directory  /srv/import
    The text field shows  processed_fs_root_directory  /srv/processed
    The datagrid cell shows  code_to_type_mapping  1  code  123
    The datagrid cell shows  code_to_type_mapping  1  portal_type  dmsincomingmail

The directories are required
    Log in as manager
    Open the batch import settings
    Click the form button  save
    The field error contains  fs_root_directory  Required input is missing.
    The field error contains  processed_fs_root_directory  Required input is missing.

A batch importer can't change the settings
    Log in as importer
    Go to  ${PLONE_URL}/@@batchimport-controlpanel
    The access is refused
