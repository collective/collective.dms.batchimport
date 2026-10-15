*** Settings ***
Documentation  Plone 6 Classic UI keywords. Same keyword names and arguments as ui_plone4.robot.
...            Robot Framework 3.0 syntax: shared with the Plone 4.3 (Python 2) environment.
...            Selectors checked on Plone 6.1 (collective.contact.contactlist) and 6.2 (collective.dms.basecontent,
...            collective.dms.mailcontent, collective.dms.batchimport).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote

*** Variables ***
${MODAL}  css=.modal-dialog
${ERROR_PAGE_TEXT}  there seems to be an error
${NOT_FOUND_TEXT}  This page does not seem to exist
${INSUFFICIENT_PRIVILEGES_TEXT}  Insufficient Privileges
# z3c.form message → message of the browser (Firefox, English) shown by pat-validation before the form is posted
&{BROWSER_VALIDATION_MESSAGES}  Required input is missing.=Please fill out this field.

*** Keywords ***
Log in with the login form
    [Documentation]  Real login (creates the user folder), unlike autologin
    [Arguments]  ${username}  ${password}
    Disable autologin
    Go to  ${PLONE_URL}/login
    Input text  css=#__ac_name  ${username}
    Input password  css=#__ac_password  ${password}
    # the login button stays disabled until the pattern of the form is initialized
    Wait until page does not contain element  css=#buttons-login.disabled
    Click button  css=#buttons-login
    Wait until page contains element  css=#personaltools-menulink

Click the content action
    [Documentation]  Item of the Actions menu (object_buttons), by action id
    [Arguments]  ${action_id}
    Click element  css=#plone-contentmenu-actions > a
    Wait until element is visible  css=#plone-contentmenu-actions-${action_id}
    Click element  css=#plone-contentmenu-actions-${action_id}

The content action is available
    [Arguments]  ${action_id}  ${expected}=${True}
    Click element  css=#plone-contentmenu-actions > a
    Wait until element is visible  css=#plone-contentmenu-actions ul
    Run keyword if  ${expected}
    ...  Page should contain element  css=#plone-contentmenu-actions-${action_id}
    ...  ELSE  Page should not contain element  css=#plone-contentmenu-actions-${action_id}

Open the add menu
    Click element  css=#plone-contentmenu-factories > a
    Wait until element is visible  css=#plone-contentmenu-factories ul

The personal action links to
    [Documentation]  Item of the user menu (user actions), by action id
    [Arguments]  ${action_id}  ${url}
    Element attribute value should be  css=#personaltools-${action_id}  href  ${url}

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
    Click button  css=.modal-footer #form-buttons-save

Cancel the modal
    Click button  css=.modal-footer #form-buttons-cancel

The modal is closed
    Wait until page does not contain element  ${MODAL}

The status message contains
    [Arguments]  ${text}
    Wait until element contains  css=.portalMessage  ${text}

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
    [Documentation]  Configlet of the Site Setup overview, by title (the icon svg has the title too: label div)
    [Arguments]  ${title}
    Click link  xpath=//ul[contains(@class, "configlets")]//a[normalize-space(div[last()])="${title}"]

Click the form button
    [Documentation]  Button of a z3c.form page, by button name (save, cancel, import…)
    [Arguments]  ${name}
    # not under the sticky form buttons, and enabled (the button is disabled until the patterns are loaded)
    Execute javascript  document.getElementById("form-buttons-${name}").scrollIntoView({block: "center", behavior: "instant"})
    Wait until page does not contain element  css=#form-buttons-${name}.disabled
    Click button  css=#form-buttons-${name}

The field error contains
    [Documentation]  Validation error shown on a field of a z3c.form page: z3c.form's message, or the browser's one
    ...              when pat-validation stopped the post (an empty input with the required attribute)
    [Arguments]  ${field_name}  ${text}
    ${locator} =  Set variable  css=#formfield-form-widgets-${field_name} .invalid-feedback
    Wait until element is visible  ${locator}
    ${error} =  Get text  ${locator}
    ${browser_text} =  Evaluate  $BROWSER_VALIDATION_MESSAGES.get($text, $text)
    Should be true  $text in $error or $browser_text in $error  Field error "${error}" contains neither "${text}" nor "${browser_text}"

Choose the file
    [Documentation]  Upload of a file widget (plone.formwidget.namedfile)
    [Arguments]  ${field_name}  ${path}
    Choose file  css=#form-widgets-${field_name}-input  ${path}

Datagrid cell
    [Documentation]  Locator of a text input of a datagrid field (collective.z3cform.datagridfield 3.x/4.x), row
    ...              from 1 (without the template row), by column name (the input id ends with -widgets-<column>)
    [Arguments]  ${field_name}  ${row}  ${column}
    ${rows} =  Set variable  //table[@id="form-widgets-${field_name}"]//tr[contains(@class, "datagridwidget-row")][not(contains(@class, "datagridwidget-empty-row"))]
    [Return]  xpath=(${rows})[${row}]//input[contains(concat(@id, "|"), "-widgets-${column}|")]

Fill the datagrid cell
    [Documentation]  Typing in the last (auto-append) row adds a new row
    [Arguments]  ${field_name}  ${row}  ${column}  ${value}
    ${cell} =  Datagrid cell  ${field_name}  ${row}  ${column}
    Execute javascript  document.getElementById("formfield-form-widgets-${field_name}").scrollIntoView({block: "center", behavior: "instant"})
    Input text  ${cell}  ${value}

The datagrid cell shows
    [Arguments]  ${field_name}  ${row}  ${column}  ${value}
    ${cell} =  Datagrid cell  ${field_name}  ${row}  ${column}
    Textfield value should be  ${cell}  ${value}
