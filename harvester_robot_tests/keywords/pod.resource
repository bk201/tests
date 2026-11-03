*** Settings ***
Documentation    Pod Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/pod_keywords.py

*** Keywords ***
Create Pod
    [Arguments]    ${name}    ${namespace}    ${spec}
    [Documentation]    Create a pod from a spec dict.
    pod_keywords.create_pod    ${name}    ${namespace}    ${spec}

Wait For Pod Succeeded
    [Arguments]    ${name}    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the pod reaches the Succeeded phase.
    pod_keywords.wait_for_pod_succeeded    ${name}    ${namespace}    ${timeout}

Get Pod Logs
    [Arguments]    ${name}    ${namespace}
    [Documentation]    Return the full log output of a pod as a string.
    ${logs}=    pod_keywords.get_pod_logs    ${name}    ${namespace}
    RETURN    ${logs}

Delete Pod If Exists
    [Arguments]    ${name}    ${namespace}
    [Documentation]    Delete a pod if it exists; silently ignores 404.
    pod_keywords.delete_pod_if_exists    ${name}    ${namespace}

Wait For Pods Running
    [Arguments]    ${namespace}    ${label}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for pods matching label to be running in namespace
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   label: Label selector for pods
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for pods with label ${label} in namespace ${namespace} to be running
    pod_keywords.wait_for_pods_running_with_label_selector    ${namespace}    ${label}    ${timeout}
    Log    Pods with label ${label} are running in ${namespace}

Wait For Pods Gone
    [Arguments]    ${namespace}    ${label}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until no pods matching the label remain in the namespace
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   label: Label selector for pods
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for pods with label ${label} in namespace ${namespace} to be gone
    pod_keywords.wait_for_pods_gone_with_label_selector    ${namespace}    ${label}    ${timeout}
    Log    No pods with label ${label} remain in ${namespace}

Pod Containers Should Use Images
    [Arguments]    ${namespace}    ${label}    ${expected}
    [Documentation]    Every pod matching the label runs each container in the
    ...    ${expected} dictionary ({container name: image}) with its image. Fails
    ...    if no pod matches.
    ${pods}=    pod_keywords.get_pod_container_images    ${namespace}    ${label}
    Should Not Be Empty    ${pods}    msg=No pods with label ${label} in ${namespace}
    FOR    ${pod}    ${containers}    IN    &{pods}
        FOR    ${container}    ${image}    IN    &{expected}
            Dictionary Should Contain Key    ${containers}    ${container}
            ...    msg=Pod ${pod} has no container ${container}: ${containers}
            Should Be Equal    ${containers}[${container}]    ${image}
            ...    msg=Pod ${pod} container ${container} runs ${containers}[${container}], expected ${image}
        END
    END
