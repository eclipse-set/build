/**
 * Starts a Github Workflow and waits for completion
 *
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param ref Git Reference to wait for (e.g. a tag name)
 * @return false if no matching workflow starts within five minutes; otherwise waits for completion and returns true
 */
def call(Map args) {
    def workflowId = ''
    for (int attempt = 0; attempt < 30; attempt++) {
        workflowId = sh(
            returnStdout: true,
            script: "gh run list --repo ${args.repo} --workflow ${args.workflow} --json headBranch,databaseId --jq '[.[] | select(.headBranch == \"${args.ref}\")][0].databaseId // empty'"
        ).trim()
        if (workflowId) {
            break
        }
        if (attempt < 29) {
            sleep time: 10, unit: 'SECONDS'
        }
    }

    if (!workflowId) {
        return false
    }

    sh "gh run watch ${workflowId} --repo ${args.repo}"
    return true
}