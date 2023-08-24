/**
 * Recreates a tag 
 *
 * Workaround for https://github.com/orgs/community/discussions/37103
 * @param repo Github Repository identifier. For example eclipse-set/model
 * @param tag Tag name to recreate
 */
def call(Map args) {
    def sha = sh(script: "gh api repos/${args.repo}/git/refs/tags -q '.[] | select(.ref | endswith(\"${args.tag}\")) | .object.sha'", returnStdout: true).trim()
    sh "gh api -X DELETE repos/${args.repo}/git/refs/tags/${args.tag}"
    sh "gh api -X POST repos/${args.repo}/git/refs -f ref=refs/tags/${args.tag} -f sha=${sha}"
}