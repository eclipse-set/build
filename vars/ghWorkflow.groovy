/**
 * Downloads a file into a target file name
 *
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param workflow Workflow yaml to run
 * @parameters List of parameters for the workflow 
 * @param citag identifier to identify the workflow run
 *
 * @author Stuecker
 */
def call(Map args) {
    def extraArgs = ""
    for (entry in args.parameters) {
        extraArgs += "-f ${entry.key}=${entry.value} "
    }

    def ref = args.ref ?: 'main'
    
    sh "gh workflow run ${args.workflow} --ref ${ref} --repo ${args.repo} -f citag=${args.citag} ${extraArgs}"
    sleep time:10, unit:"SECONDS"
    def workflowId = sh(returnStdout: true, script: "gh run list --workflow=${args.workflow} --repo ${args.repo} --json displayTitle,databaseId --jq '.[] | select(.displayTitle | endswith(\"${args.citag}\")) | .databaseId'").trim()

    sh "gh run watch ${workflowId} --repo ${args.repo}"
}