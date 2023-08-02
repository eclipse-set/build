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
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import org.apache.maven.artifact.handler.manager.ArtifactHandlerManager;
import org.apache.maven.artifact.repository.ArtifactRepository;
import org.apache.maven.artifact.repository.ArtifactRepositoryPolicy;
import org.apache.maven.artifact.repository.MavenArtifactRepository;
import org.apache.maven.artifact.repository.layout.ArtifactRepositoryLayout;
import org.apache.maven.execution.MavenSession;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.MojoFailureException;
import org.apache.maven.plugins.annotations.Component;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.project.DefaultProjectBuildingRequest;
import org.apache.maven.project.ProjectBuildingRequest;
import org.apache.maven.repository.RepositorySystem;
import org.apache.maven.settings.Settings;
import org.apache.maven.shared.transfer.artifact.DefaultArtifactCoordinate;
import org.apache.maven.shared.transfer.artifact.resolve.ArtifactResolver;
import org.apache.maven.shared.transfer.artifact.resolve.ArtifactResolverException;
import org.apache.maven.shared.transfer.artifact.resolve.ArtifactResult;

@Mojo(name = "fetch", requiresProject = false, threadSafe = true, defaultPhase = LifecyclePhase.GENERATE_RESOURCES)
public class MavenRootfilesMojo extends AbstractMojo {
	@Parameter(defaultValue = "${session}", required = true, readonly = true)
	private MavenSession session;
	
	@Component
	private ArtifactResolver artifactResolver;

	@Component
	private ArtifactHandlerManager artifactHandlerManager;

	@Component(role = ArtifactRepositoryLayout.class)
	private Map<String, ArtifactRepositoryLayout> repositoryLayouts;

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

	@Override
	public void execute() throws MojoExecutionException, MojoFailureException {
		ArtifactRepositoryPolicy always = new ArtifactRepositoryPolicy(true,
				ArtifactRepositoryPolicy.UPDATE_POLICY_ALWAYS, ArtifactRepositoryPolicy.CHECKSUM_POLICY_WARN);

		ArtifactRepositoryLayout layout = repositoryLayouts.get("default");
		List<ArtifactRepository> repoList = List
				.of(new MavenArtifactRepository(serverId, serverUrl, layout, always, always));

		try {
			ProjectBuildingRequest buildingRequest = new DefaultProjectBuildingRequest(
					session.getProjectBuildingRequest());

			Settings settings = session.getSettings();
			repositorySystem.injectMirror(repoList, settings.getMirrors());
			repositorySystem.injectProxy(repoList, settings.getProxies());
			repositorySystem.injectAuthentication(repoList, settings.getServers());

			buildingRequest.setRemoteRepositories(repoList);

			DefaultArtifactCoordinate coordinate = new DefaultArtifactCoordinate();
			coordinate.setGroupId(groupId);
			coordinate.setArtifactId(artifactId);
			coordinate.setVersion(version);
			coordinate.setClassifier("root");
			coordinate.setExtension("zip");

			getLog().info("Resolving " + coordinate);
			ArtifactResult artifactResult = artifactResolver.resolveArtifact(buildingRequest, coordinate);

			getLog().info("Extracting " + artifactResult.getArtifact().getFile().getAbsolutePath());
			unzip(artifactResult.getArtifact().getFile(), new File(outPath));
		} catch (ArtifactResolverException e) {
			throw new MojoExecutionException("Couldn't download artifact: " + e.getMessage(), e);
		} catch (IOException e) {
			throw new MojoExecutionException("Couldn't extract artifact: " + e.getMessage(), e);
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
