/**
 * Copyright (c) 2023 DB Netz AG and others.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v20.html
 */
package org.eclipse.set.rootfilesmavenplugin;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import org.apache.maven.artifact.handler.manager.ArtifactHandlerManager;
import org.apache.maven.execution.MavenSession;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.MojoFailureException;
import org.apache.maven.plugins.annotations.Component;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.apache.maven.shared.transfer.artifact.resolve.ArtifactResolver;
import org.eclipse.aether.RepositorySystem;
import org.eclipse.aether.RepositorySystemSession;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.repository.RemoteRepository;
import org.eclipse.aether.resolution.ArtifactRequest;
import org.eclipse.aether.resolution.ArtifactResolutionException;
import org.eclipse.aether.resolution.ArtifactResult;

@Mojo(name = "fetch", requiresProject = false, threadSafe = true, defaultPhase = LifecyclePhase.GENERATE_RESOURCES, requiresDependencyResolution = ResolutionScope.COMPILE_PLUS_RUNTIME)
public class MavenRootfilesMojo extends AbstractMojo {
	@Parameter(defaultValue = "${session}", required = true, readonly = true)
	private MavenSession session;

	@Parameter(defaultValue = "${project}", readonly = true)
	private MavenProject project;

	@Component
	private ArtifactResolver artifactResolver;

	@Component
	private ArtifactHandlerManager artifactHandlerManager;

	@Component
	private RepositorySystem repositorySystem;

	@Parameter(property = "serverId", required = true)
	private String serverId;

	@Parameter(property = "serverUrl", required = true)
	private String serverUrl;

	@Parameter(property = "groupId", required = true)
	private String groupId;

	@Parameter(property = "artifactId", required = true)
	private String artifactId;

	@Parameter(property = "version", required = true)
	private String version;

	@Parameter(property = "outPath", required = true)
	private String outPath;

	@Parameter(defaultValue = "${repositorySystemSession}", readonly = true, required = true)
	private RepositorySystemSession repoSession;

	@Override
	public void execute() throws MojoExecutionException, MojoFailureException {
		try {
			org.eclipse.aether.artifact.Artifact artifact = new DefaultArtifact(groupId, artifactId, "root", "zip",
					version);

			List<RemoteRepository> remoteRepositories = repositorySystem.newResolutionRepositories(repoSession,
					List.of(new RemoteRepository.Builder(serverId, "default", serverUrl).build()));
			getLog().info("Resolving " + artifact);
			ArtifactRequest resolveRequest = new ArtifactRequest(artifact, remoteRepositories, null);
			ArtifactResult artifactResult = repositorySystem.resolveArtifact(repoSession, resolveRequest);
			getLog().info("Extracting " + artifactResult.getArtifact().getFile().getAbsolutePath());
			unzip(artifactResult.getArtifact().getFile(), new File(outPath));
		} catch (IOException e) {
			throw new MojoExecutionException("Couldn't extract artifact: " + e.getMessage(), e);
		} catch (ArtifactResolutionException e) {
			throw new MojoExecutionException("Couldn't download artifact: " + e.getMessage(), e);
		}
	}

	private void unzip(File zipFile, File outDir) throws IOException {
		byte[] buffer = new byte[1024];

		try (ZipInputStream zis = new ZipInputStream(new FileInputStream(zipFile))) {
			ZipEntry zipEntry = zis.getNextEntry();
			while (zipEntry != null) {
				File newFile = new File(outDir, zipEntry.getName());
				if (zipEntry.isDirectory()) {
					if (!newFile.isDirectory() && !newFile.mkdirs()) {
						throw new IOException("Failed to create directory " + newFile);
					}
				} else {
					try (FileOutputStream fos = new FileOutputStream(newFile)) {
						int len = 0;
						while ((len = zis.read(buffer)) > 0) {
							fos.write(buffer, 0, len);
						}
					}
				}
				zipEntry = zis.getNextEntry();
			}
			zis.closeEntry();
		}
	}

}
