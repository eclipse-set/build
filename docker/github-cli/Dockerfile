FROM debian:bookworm-slim

RUN set -ex; \
    apt-get update ; \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git; \
    rm -rf /var/lib/apt/lists/*

ENV GITHUB_CLI_VERSION 2.32.1

RUN curl -OL "https://github.com/cli/cli/releases/download/v${GITHUB_CLI_VERSION}/gh_${GITHUB_CLI_VERSION}_linux_amd64.deb"; \
	dpkg -i "gh_${GITHUB_CLI_VERSION}_linux_amd64.deb"; \
	rm -rf "gh_${GITHUB_CLI_VERSION}_linux_amd64.deb"