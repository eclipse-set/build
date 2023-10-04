/**
 * Copyright (c) 2023 DB Netz AG and others.
 * 
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v20.html
 */
package org.eclipse.set.planpromavenplugin;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.io.FileUtils;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.MojoFailureException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;

/**
 * 
 */
@Mojo(name = "transform", requiresProject = false, threadSafe = true, defaultPhase = LifecyclePhase.PROCESS_CLASSES)
public class MavenReleaseNotesMojo extends AbstractMojo {

	private static String versionNumberReg = "^##\\s*\\d+\\.\\d+";

	@SuppressWarnings("boxing")
	private static String createAcsiidocHeader(final int index,
			final String versionNumber) {
		return String.format("title: \"%s\"\nanchor: \"%s\"\nWeight: %d",
				versionNumber, versionNumber, index + 1);
	}

	private static String createAsiidoc(final int index,
			final String versionNumber, final String notes) {
		return String.format("---\n%s\n---\n++++\n%s\n++++",
				createAcsiidocHeader(index, versionNumber), notes);
	}

	private static String transformNotes(final String line) {
		if (line.startsWith("-")) {
			return String.format("<li>%s</li>", line.replace("-", ""));
		}
		return line + "<br/>";
	}

	@SuppressWarnings("boxing")
	private static Map<String, String> transformToAsciidoc(
			final Map<String, List<String>> releaseNotes) {
		final Map<String, String> result = new LinkedHashMap<>();
		int index = 0;
		for (final Entry<String, List<String>> notes : releaseNotes
				.entrySet()) {
			final Set<Integer> liElementIndex = new HashSet<>();
			notes.getValue().forEach(ele -> {
				if (ele.startsWith("<li>")) {
					liElementIndex.add(
							Integer.valueOf(notes.getValue().indexOf(ele)));
				}
			});
			final int liElementLastIndex = liElementIndex.stream()
					.max(Integer::compare).orElse(notes.getValue().size() - 1)
					+ 1;
			final int liElementFirstIndex = liElementIndex.stream()
					.min(Integer::compare).orElse(0);
			notes.getValue().add(liElementLastIndex, "</ul>");
			notes.getValue().add(liElementFirstIndex, "<ul>");
			result.put(notes.getKey(), createAsiidoc(index, notes.getKey(),
					String.join("", notes.getValue())));
			index++;
		}
		return result;
	}

	@Parameter(property = "notesPath", required = true)
	private String notesPath;

	@Parameter(property = "outDir", required = true)
	private String outDir;

	@Override
	public void execute() throws MojoExecutionException, MojoFailureException {
		try {
			getLog().info("Transforming RELASE_NOTE.md");
			final Map<String, List<String>> releaseNotes = readReleaseNote();
			final Map<String, String> asciidocs = transformToAsciidoc(
					releaseNotes);
			asciidocs.forEach((t, u) -> {
				try {
					writeFile(t, u);
				} catch (final IOException e) {
					throw new RuntimeException(e);
				}
			});
		} catch (final IOException e) {
			throw new RuntimeException(e);
		}
	}

	private Map<String, List<String>> readReleaseNote() throws IOException {
		getLog().info("Read RELASE_NOTE.md");
		final Map<String, List<String>> result = new LinkedHashMap<>();
		try (final BufferedReader reader = Files
				.newBufferedReader(Paths.get(notesPath))) {
			String currentVersion = "";
			final Pattern pattern = Pattern.compile(versionNumberReg);
			while (reader.ready()) {
				final String line = reader.readLine();
				if (line.isEmpty()) {
					continue;
				}

				final Matcher matcher = pattern.matcher(line);
				if (matcher.matches()) {
					currentVersion = line.replace("#", "").trim();
					result.put(currentVersion, new LinkedList<>());
				} else if (!currentVersion.isEmpty()) {
					result.get(currentVersion).add(transformNotes(line));
				}
			}
		}
		return result;
	}

	private void writeFile(final String versionNumber, final String doc)
			throws IOException {
		final Path path = Paths.get(outDir, versionNumber, "_index.adoc");
		if (!Files.exists(path.getParent())) {
			path.getParent().toFile().mkdirs();
		}
		getLog().info("Write file: " + path.toString());
		FileUtils.writeStringToFile(path.toFile(), doc, StandardCharsets.UTF_8);
	}

}
