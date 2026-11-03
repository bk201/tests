*** Settings ***
Documentation    Support Bundle Keywords
Library          ../libs/keywords/support_bundle_keywords.py
Library          ../libs/keywords/setting_keywords.py
Resource         variables.resource
Resource         helm_release.resource
Resource         pod.resource


*** Variables ***
${SUPPORT_BUNDLE_NAMESPACE}         harvester-system
${SUPPORT_BUNDLE_IMAGE_SETTING}     support-bundle-image
${SUPPORT_BUNDLE_IMAGE_PATH}        support-bundle-kit.image


*** Keywords ***
Support Bundle Image Setting Is Cleared
    [Documentation]    Save the support-bundle-image setting, then clear it, so the
    ...    next support bundle resolves the image from the harvester chart again.
    ...    Restore it with `Restore Support Bundle Image Setting`.
    ${setting}=    setting_keywords.get    ${SUPPORT_BUNDLE_IMAGE_SETTING}
    ${default}=    Get From Dictionary    ${setting}    default    default=${EMPTY}
    ${value}=    Get From Dictionary    ${setting}    value    default=${EMPTY}
    ${saved}=    Create Dictionary    default=${default}    value=${value}
    Set Suite Variable    ${SAVED_SUPPORT_BUNDLE_IMAGE_SETTING}    ${saved}
    setting_keywords.update    ${SUPPORT_BUNDLE_IMAGE_SETTING}    ${EMPTY}
    setting_keywords.update_default    ${SUPPORT_BUNDLE_IMAGE_SETTING}    {}

Restore Support Bundle Image Setting
    [Documentation]    Restore the setting saved by `Support Bundle Image Setting Is Cleared`
    ${saved}=    Get Variable Value    ${SAVED_SUPPORT_BUNDLE_IMAGE_SETTING}    ${None}
    IF    $saved is not None
        setting_keywords.update_default    ${SUPPORT_BUNDLE_IMAGE_SETTING}    ${saved}[default]
        setting_keywords.update    ${SUPPORT_BUNDLE_IMAGE_SETTING}    ${saved}[value]
    END

Support Bundle Is Created
    [Arguments]    ${name}
    support_bundle_keywords.create_support_bundle    ${name}    Created by the robot tests

Support Bundle Should Be Ready
    [Arguments]    ${name}
    support_bundle_keywords.wait_for_support_bundle_ready    ${name}    ${WAIT_TIMEOUT}

Delete Support Bundle If Exists
    [Arguments]    ${name}
    support_bundle_keywords.delete_support_bundle_if_exists    ${name}

Get Harvester Support Bundle Image
    [Documentation]    Return the support bundle image in the harvester chart values
    ${image}=    Get Helm Release Image    ${SUPPORT_BUNDLE_NAMESPACE}    harvester
    ...    ${SUPPORT_BUNDLE_IMAGE_PATH}
    RETURN    ${image}

Support Bundle Image Setting Should Be Filled
    [Documentation]    The support bundle controller has filled the setting's default
    ${default}=    setting_keywords.get_default    ${SUPPORT_BUNDLE_IMAGE_SETTING}
    Should Not Be Equal    ${default}    {}    msg=${SUPPORT_BUNDLE_IMAGE_SETTING} default is still empty

Support Bundle Image Setting Should Match Harvester Chart
    [Documentation]    The setting's default is the support bundle image of the
    ...    harvester chart, pull policy included
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Support Bundle Image Setting Should Be Filled
    ${expected}=    Get Harvester Support Bundle Image
    ${default}=    setting_keywords.get_default    ${SUPPORT_BUNDLE_IMAGE_SETTING}
    ${actual}=    Evaluate    json.loads($default)    modules=json
    Should Be Equal    ${actual}[repository]    ${expected}[repository]
    Should Be Equal As Strings    ${actual}[tag]    ${expected}[tag]
    Should Be Equal    ${actual}[imagePullPolicy]    ${expected}[imagePullPolicy]

Support Bundle Manager Should Use Harvester Chart Image
    [Arguments]    ${name}
    ${expected}=    Get Harvester Support Bundle Image
    ${selector}=    Set Variable    app\=support-bundle-manager,rancher/supportbundle\=${name}
    ${images}=    Create Dictionary    manager=${expected}[image]
    Pod Containers Should Use Images    ${SUPPORT_BUNDLE_NAMESPACE}    ${selector}    ${images}
