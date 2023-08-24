/**
 * Creates a tag and waits for the gh build to complete
 *
 * Workaround for https://github.com/orgs/community/discussions/37103
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param ref branch to tag from. Must not be main
 * @param version version to tag for
 */
def call(Map args) {
    ghWorkflow workflow: 'create-release-tag.yml', repo: args.repo, ref: args.ref, citag: "[${args.version}]", parameters: [version: args.version]
    // Workaround for https://github.com/orgs/community/discussions/37103
    // delete tag and recreate with same ref to trigger gh actions
    ghRecreateTag repo: args.repo, tag: "v${args.version}"
    // Wait for build to start
    sleep time:10, unit:"SECONDS"
    ghWaitForRefBuild repo: args.repo, ref: "v${args.version}"
}