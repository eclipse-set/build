/**
 * Starts a Github Workflow and waits for completion
 *
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param ref Git Reference to wait for (e.g. a tag name)
 */
def call(Map args) {
    def workflowId = sh(returnStdout: true, script: "gh run list --repo ${args.repo} --json headBranch,databaseId --jq '.[] | select(.headBranch | startswith(\"${args.ref}\")) | .databaseId'").trim()
    sh "gh run watch ${workflowId} --repo ${args.repo}"
}