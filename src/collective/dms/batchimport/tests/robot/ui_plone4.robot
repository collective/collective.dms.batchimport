*** Settings ***
Documentation  Plone 4.3 keywords. Same keyword names and arguments as ui_plone6.robot.
...            Robot Framework 3.0 syntax (Python 2 environment).
...            Selectors checked on Plone 4.3 (imio.annex, collective.dms.basecontent, collective.dms.mailcontent,
...            collective.dms.batchimport).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote

*** Variables ***
${MODAL}  css=div.overlay-ajax
${ERROR_PAGE_TEXT}  there seems to be an error
${NOT_FOUND_TEXT}  This page does not seem to exist
${INSUFFICIENT_PRIVILEGES_TEXT}  Insufficient Privileges

*** Keywords ***
Log in with the login form
    [Documentation]  Real login (creates the user folder), unlike autologin
    [Arguments]  ${username}  ${password}
    Disable autologin
    Go to  ${PLONE_URL}/login_form
    Input text  css=#__ac_name  ${username}
    Input password  css=#__ac_password  ${password}
    Click button  css=input[name="submit"]
    # #portal-personaltools is also shown to anonymous users
    Wait until page contains element  css=#user-name

Click the content action
    [Documentation]  Item of the Actions menu (object_buttons), by action id
    [Arguments]  ${action_id}
    Click element  css=#plone-contentmenu-actions dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-actions-${action_id}
    Click element  css=#plone-contentmenu-actions-${action_id}

The content action is available
    [Arguments]  ${action_id}  ${expected}=${True}
    Click element  css=#plone-contentmenu-actions dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-actions dd.actionMenuContent
    Run keyword if  ${expected}
    ...  Page should contain element  css=#plone-contentmenu-actions-${action_id}
    ...  ELSE  Page should not contain element  css=#plone-contentmenu-actions-${action_id}

Open the add menu
    Click element  css=#plone-contentmenu-factories dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-factories dd.actionMenuContent

The personal action links to
    [Documentation]  Item of the user menu (user actions), by action id
    [Arguments]  ${action_id}  ${url}
    Element attribute value should be  css=#personaltools-${action_id} a  href  ${url}

The personal action is not available
    [Arguments]  ${action_id}
    Page should not contain element  css=#personaltools-${action_id}

The modal is open
    [Documentation]  Overlay (Plone 4) or modal (Plone 6) showing a form
    Wait until element is visible  ${MODAL} form

Modal element
    [Documentation]  Locator of the element with this id inside the modal
    ...              (an argument starting with # would be a robot comment)
    [Arguments]  ${id}
    [Return]  ${MODAL} [id="${id}"]

Save the modal
    Click button  ${MODAL} #form-buttons-save

Cancel the modal
    Click button  ${MODAL} #form-buttons-cancel

The modal is closed
    Wait until element is not visible  ${MODAL}

The status message contains
    [Arguments]  ${text}
    # skip the hidden #kssPortalMessage
    Wait until element contains  css=.portalMessage:not(#kssPortalMessage)  ${text}

The page is not an error
    Page should not contain  ${ERROR_PAGE_TEXT}

The page is not found
    Page should contain  ${NOT_FOUND_TEXT}

The edit link is not available
    Page should not contain element  css=#contentview-edit

The access is refused
    [Documentation]  Page shown to an authenticated user without the permission
    Page should contain  ${INSUFFICIENT_PRIVILEGES_TEXT}

Click the control panel link
    [Documentation]  Configlet of the Site Setup overview, by title
    [Arguments]  ${title}
    Click link  xpath=//a[normalize-space()="${title}"]

Click the form button
    [Documentation]  Button of a z3c.form page, by button name (save, cancel, import…)
    [Arguments]  ${name}
    Click button  css=#form-buttons-${name}

The field error contains
    [Documentation]  Validation error shown on a field of a z3c.form page
    [Arguments]  ${field_name}  ${text}
    Element should contain  css=#formfield-form-widgets-${field_name} .fieldErrorBox  ${text}

Choose the file
    [Documentation]  Upload of a file widget (plone.formwidget.namedfile)
    [Arguments]  ${field_name}  ${path}
    Choose file  css=#form-widgets-${field_name}-input  ${path}

Datagrid cell
    [Documentation]  Locator of a text input of a datagrid field (collective.z3cform.datagridfield 1.x), row from 1
    ...              (without the hidden template row), by column name (the input id ends with -widgets-<column>)
    [Arguments]  ${field_name}  ${row}  ${column}
    ${rows} =  Set variable  //table[@id="form-widgets-${field_name}"]//tr[contains(@class, "datagridwidget-row")][not(contains(@class, "datagridwidget-empty-row"))]
    [Return]  xpath=(${rows})[${row}]//input[contains(concat(@id, "|"), "-widgets-${column}|")]

Fill the datagrid cell
    [Documentation]  Typing in the last (auto-append) row adds a new row
    [Arguments]  ${field_name}  ${row}  ${column}  ${value}
    ${cell} =  Datagrid cell  ${field_name}  ${row}  ${column}
    Input text  ${cell}  ${value}

The datagrid cell shows
    [Arguments]  ${field_name}  ${row}  ${column}  ${value}
    ${cell} =  Datagrid cell  ${field_name}  ${row}  ${column}
    Textfield value should be  ${cell}  ${value}
