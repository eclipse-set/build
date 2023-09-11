/**
 * Copyright (c) 2023 DB Netz AG and others.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v20.html
 */
package org.eclipse.set.licensemavenplugin;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collection;

import org.eclipse.dash.licenses.IContentId;
import org.eclipse.dash.licenses.cli.FlatFileReader;
import org.eclipse.dash.licenses.cli.IDependencyListReader;
import org.eclipse.dash.licenses.cli.PackageLockFileReader;

/** 
 * Helper class to add all dependencies from *.deps and package-lock.json files
 */
public class ExtraDependencies {
	
	public static Collection<IContentId> getDependencies(Path path) {
		try {
			return getReader(path.toAbsolutePath()).getContentIds();
		} catch (FileNotFoundException e) {
			throw new RuntimeException(e);
		}
	}

	private static IDependencyListReader getReader(Path path) throws FileNotFoundException {
		File input = path.toFile();
		if (input.exists()) {
			if ("package-lock.json".equals(input.getName())) {
				return new PackageLockFileReader(new FileInputStream(input));
			}
			return new FlatFileReader(new FileReader(input));
		} else {
			throw new FileNotFoundException(path.toString());
		}
	}
	
	public static Collection<? extends IContentId> getExtraDependencies() {
		try {
			return Files.find(Paths.get("."), 100, (path, attrs) -> attrs.isRegularFile())
			.filter(p -> p.endsWith(".deps") || p.getFileName().toString().equals("package-lock.json"))
			.map(ExtraDependencies::getDependencies)
			.flatMap(Collection::stream)
			.toList();
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
	}

}
