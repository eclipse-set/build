/**
 * Creates a tag and waits for the gh build to complete
 *
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param ref branch to tag from. Must not be main
 * @param version version to tag for
 */
def call(Map args) {
    ghWorkflow workflow: 'create-release-tag.yml', repo: args.repo, ref: args.ref, citag: "[${args.version}]", parameters: [version: args.version]

    def tag = "v${args.version}"
    if (!ghWaitForRefBuild(repo: args.repo, ref: tag)) {
        // Workaround for https://github.com/orgs/community/discussions/37103
        ghRecreateTag repo: args.repo, tag: tag
        if (!ghWaitForRefBuild(repo: args.repo, ref: tag, workflow: args.workflow)) {
            throw new IllegalStateException("No workflow started for tag ${tag} after recreating it")
        }
    }
}