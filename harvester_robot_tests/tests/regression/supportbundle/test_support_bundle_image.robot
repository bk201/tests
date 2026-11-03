*** Settings ***
Documentation    Support bundle image
...    The support bundle controller resolves the support-bundle-kit image from
...    the harvester chart values (helm.FetchImageFromHelmValues) when the
...    support-bundle-image setting is empty, and stores it in the setting's
...    default. The suite clears the setting, generates a bundle, and checks the
...    setting and the manager pod against the harvester release's values.
...    It changes a cluster-wide setting, so it isn't parallel-safe. CRD only.
Test Tags        support-bundle

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/support_bundle.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${BUNDLE_NAME}    ${EMPTY}


*** Test Cases ***
Support Bundle Resolves Its Image From The Harvester Chart
    [Tags]    p1
    [Documentation]    With the support-bundle-image setting cleared, generating a
    ...    support bundle fills the setting from the harvester chart, and the
    ...    manager runs that image
    Given Support Bundle Image Setting Is Cleared
    When Support Bundle Is Created    ${BUNDLE_NAME}
    Then Support Bundle Image Setting Should Match Harvester Chart
    And Support Bundle Should Be Ready    ${BUNDLE_NAME}
    And Support Bundle Manager Should Use Harvester Chart Image    ${BUNDLE_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${BUNDLE_NAME}    sb-${suffix}
    Set up test environment

Local Suite Teardown
    # Always restore the setting: it's cluster-wide.
    Run Keyword And Ignore Error    Restore Support Bundle Image Setting
    Run Keyword If All Tests Passed    Run Keyword And Ignore Error
    ...    Delete Support Bundle If Exists    ${BUNDLE_NAME}
    Run Keyword If Any Tests Failed    Log Variables
