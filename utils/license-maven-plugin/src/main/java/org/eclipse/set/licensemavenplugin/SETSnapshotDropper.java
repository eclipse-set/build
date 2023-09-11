/**
 * Copyright (c) 2023 DB Netz AG and others.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v20.html
 */
package org.eclipse.set.licensemavenplugin;

import java.util.regex.Pattern;

import org.eclipse.dash.licenses.ContentId;
import org.eclipse.dash.licenses.IContentId;

/**
 * Helper class to drop the snapshot version from SET artifacts to reduce noise
 */
public class SETSnapshotDropper {
	static boolean isP2Dependency(IContentId contentId) 
	{
		return contentId.getType().equals("p2") && contentId.getSource().equals("orbit") && contentId.getNamespace().equals("p2.eclipse.plugin"); 
	}
	
	static IContentId mapDependency(IContentId contentId) {
		// Only consider p2 dependencies
		if(!isP2Dependency(contentId))
			return contentId;
		
		// Only consider Eclipse SET artifacts
		String name = contentId.getName();
		if(!name.startsWith("org.eclipse.set."))
			return contentId;
		
		// Drop the timestamp from the dependencies 
		final String[] versionParts = contentId.getVersion().split(Pattern.quote("."));
		final String version = versionParts[0] + "." + versionParts[1] + "." + versionParts[2];
		
		return ContentId.getContentId(contentId.getType(), contentId.getSource(), contentId.getNamespace(), contentId.getName(), version);	
	}
}
