*** Settings ***
Documentation    Helm Release Keywords
...    Read the values of deployed Helm releases, chart defaults included, to
...    get the images that Harvester controllers resolve from them.
Library          ../libs/keywords/helm_release_keywords.py

*** Keywords ***
Get Helm Release Image
    [Arguments]    ${namespace}    ${release}    ${path}    ${registry}=${EMPTY}
    [Documentation]    Return the image at the dotted path of a release's values as
    ...    a dict with repository, tag, imagePullPolicy and image, where image is
    ...    [<registry>/]<repository>:<tag>.
    ${image}=    helm_release_keywords.get_helm_release_image
    ...    ${namespace}    ${release}    ${path}    ${registry}
    RETURN    ${image}
