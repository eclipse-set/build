/**
 * Copyright (c) 2023 DB Netz AG and others.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v20.html
 */
package org.eclipse.set.planpromavenplugin;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import org.apache.maven.RepositoryUtils;
import org.apache.maven.artifact.handler.manager.ArtifactHandlerManager;
import org.apache.maven.artifact.repository.ArtifactRepository;
import org.apache.maven.artifact.repository.ArtifactRepositoryPolicy;
import org.apache.maven.artifact.repository.MavenArtifactRepository;
import org.apache.maven.artifact.repository.layout.ArtifactRepositoryLayout;
import org.apache.maven.artifact.repository.metadata.Snapshot;
import org.apache.maven.artifact.repository.metadata.SnapshotVersion;
import org.apache.maven.artifact.repository.metadata.Versioning;
import org.apache.maven.artifact.repository.metadata.io.xpp3.MetadataXpp3Reader;
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
import org.eclipse.aether.RepositorySystemSession;
import org.eclipse.aether.RequestTrace;
import org.eclipse.aether.SyncContext;
import org.eclipse.aether.artifact.Artifact;
import org.eclipse.aether.artifact.DefaultArtifact;
import org.eclipse.aether.impl.MetadataResolver;
import org.eclipse.aether.impl.SyncContextFactory;
import org.eclipse.aether.impl.VersionResolver;
import org.eclipse.aether.metadata.DefaultMetadata;
import org.eclipse.aether.metadata.Metadata;
import org.eclipse.aether.repository.LocalRepository;
import org.eclipse.aether.repository.RemoteRepository;
import org.eclipse.aether.repository.RemoteRepository.Builder;
import org.eclipse.aether.resolution.ArtifactDescriptorRequest;
import org.eclipse.aether.resolution.MetadataRequest;
import org.eclipse.aether.resolution.MetadataResult;

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
	private VersionResolver versionResolver;

	@Component
	private SyncContextFactory syncContextFactory;

	@Component
	private MetadataResolver metadataResolver;

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

	private static final String RELEASE = "RELEASE";
	private static final String LATEST = "LATEST";
	private static final String SNAPSHOT = "SNAPSHOT";
	private static final String MAVEN_METADATA_XML = "maven-metadata.xml";

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
			String detailVersion = resolveVersion(buildingRequest, version);
			coordinate.setGroupId(groupId);
			coordinate.setArtifactId(artifactId);
			coordinate.setVersion(detailVersion);
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

	private String resolveVersion(ProjectBuildingRequest buildingRequest, String targetVersion) {
		Metadata metadata = createDefaultMetaData(targetVersion);
		if (metadata == null) {
			return targetVersion;
		}
		RepositorySystemSession repoSession = buildingRequest.getRepositorySession();
		Builder builder = new RemoteRepository.Builder(serverId, serverUrl, "default");
		MetadataRequest metadataRequest = new MetadataRequest(metadata);
		metadataRequest.setRepository(builder.build());
		Versioning versioning = null;
		for (MetadataResult metadataResult : resolveMetadata(metadata, buildingRequest, targetVersion)) {
			org.eclipse.aether.repository.ArtifactRepository repository = metadataResult.getRequest().getRepository();
			if (repository == null) {
				repository = repoSession.getLocalRepository();
			}
			versioning = readVersions(repoSession, metadataResult.getMetadata(), repository);
			Optional<SnapshotVersion> rootArtifactVersion = getRootArtifactVersion(versioning);
			if (rootArtifactVersion.isPresent()) {
				return rootArtifactVersion.get().getVersion();
			}
		}
		if (versioning != null) {
			if (RELEASE.equals(targetVersion) && versioning.getRelease() != null
					&& !versioning.getRelease().isEmpty()) {
				return versioning.getRelease();
			}

			if (LATEST.equals(targetVersion) && versioning.getLatest() != null && !versioning.getLatest().isEmpty()) {
				return resolveVersion(buildingRequest, versioning.getLatest());
			}
		}
		return version;
	}

	private Metadata createDefaultMetaData(String targetVersion) {
		if (RELEASE.equals(targetVersion)) {
			return new DefaultMetadata(groupId, artifactId, MAVEN_METADATA_XML, Metadata.Nature.RELEASE);
		} else if (LATEST.equals(targetVersion)) {
			return new DefaultMetadata(groupId, artifactId, MAVEN_METADATA_XML, Metadata.Nature.RELEASE_OR_SNAPSHOT);
		} else if (targetVersion.endsWith(SNAPSHOT)) {
			return new DefaultMetadata(groupId, artifactId, targetVersion, MAVEN_METADATA_XML,
					Metadata.Nature.SNAPSHOT);
		}
		return null;
	}

	private List<MetadataResult> resolveMetadata(Metadata defaultMetadata, ProjectBuildingRequest buildingRequest,
			String targetVersion) {
		List<RemoteRepository> repos = RepositoryUtils.toRepos(buildingRequest.getRemoteRepositories());
		Artifact aetherArtifact = new DefaultArtifact(groupId, artifactId, "zip", targetVersion);
		ArtifactDescriptorRequest descriptorRequest = new ArtifactDescriptorRequest(aetherArtifact, repos, null);

		List<MetadataRequest> metadataRequests = new ArrayList<>(repos.size());
		metadataRequests.add(new MetadataRequest(defaultMetadata, null, null));
		for (RemoteRepository repo : repos) {
			MetadataRequest metadataRequest = new MetadataRequest(defaultMetadata, repo, null);
			metadataRequest.setDeleteLocalCopyIfMissing(true);
			metadataRequest.setFavorLocalRepository(true);
			metadataRequest.setTrace(RequestTrace.newChild(descriptorRequest.getTrace(), descriptorRequest));
			metadataRequests.add(metadataRequest);
		}

		return metadataResolver.resolveMetadata(buildingRequest.getRepositorySession(), metadataRequests);
	}

	private Versioning readVersions(RepositorySystemSession session, Metadata metadata,
			org.eclipse.aether.repository.ArtifactRepository repository) {
		Versioning versioning = null;
		if (metadata == null) {
			return new Versioning();
		}
		try (SyncContext syncContext = syncContextFactory.newInstance(session, true)) {
			syncContext.acquire(null, Collections.singleton(metadata));
			if (metadata.getFile() != null && metadata.getFile().exists()) {
				try (InputStream in = new FileInputStream(metadata.getFile())) {
					versioning = new MetadataXpp3Reader().read(in, false).getVersioning();
					if (versioning != null && repository instanceof LocalRepository && versioning.getSnapshot() != null
							&& versioning.getSnapshot().getBuildNumber() > 0) {
						Versioning repaired = new Versioning();
						repaired.setLastUpdated(versioning.getLastUpdated());
						repaired.setSnapshot(new Snapshot());
						repaired.getSnapshot().setLocalCopy(true);
						versioning = repaired;
						throw new IOException("Snapshot information corrupted with remote repository data"
								+ ", please verify that no remote repository uses the id '" + repository.getId() + "'");
					}
				}
			}
		} catch (Exception e) {
			getLog().info("ERROR " + e.getMessage());
		}
		return versioning == null ? new Versioning() : versioning;
	}

	private Optional<SnapshotVersion> getRootArtifactVersion(Versioning versioning) {
		return versioning.getSnapshotVersions().stream().filter(Objects::nonNull).filter(snapShotVersion -> {
			String key = "";
			if (!snapShotVersion.getClassifier().isBlank()) {
				key = snapShotVersion.getClassifier() + "." + snapShotVersion.getExtension();
			} else {
				key = snapShotVersion.getExtension();
			}
			return key.endsWith("root.zip");
		}).findFirst();
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
