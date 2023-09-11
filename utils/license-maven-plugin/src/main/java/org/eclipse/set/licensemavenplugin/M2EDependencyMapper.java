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
 * Helper class to map M2E-wrapped dependencies to their original maven counterparts 
 */
public class M2EDependencyMapper {
	static boolean isP2Dependency(IContentId contentId) 
	{
		return contentId.getType().equals("p2") && contentId.getSource().equals("orbit") && contentId.getNamespace().equals("p2.eclipse.plugin"); 
	}
	
	static IContentId mapDependency(IContentId contentId) {
		// Only consider p2 dependencies
		if(!isP2Dependency(contentId))
			return contentId;
		
		final String PREFIX = "maven.";
		final String INFIX = ".artifact.";
		
		// By convention, a M2E-wrapped artifact is of the format maven.<groupId>.artifact.<artifactId>
		String name = contentId.getName();
		if(!name.startsWith(PREFIX) || !name.contains(INFIX))
			return contentId;
		
		// Extract the original maven gid/aid pair
		String noPrefixName = name.substring(PREFIX.length());
		String[] parts = noPrefixName.split(Pattern.quote(INFIX));
		System.out.println(noPrefixName);
		System.out.println(parts.length);
		final String groupId = parts[0];
		final String artifactId = parts[1];		
		String version = contentId.getVersion();
		
		// Extra case: Apache FOP on Maven Central only has <major>.<minor> versions. M2E creates <major>.<minor>.<patch> 
		if(groupId.equals("org.apache.xmlgraphics") && artifactId.equals("fop"))
		{
			String[] versionParts = version.split(Pattern.quote("."));
			version = versionParts[0] + "." + versionParts[1];
		}
				
		
		return ContentId.getContentId("maven", "mavencentral", groupId, artifactId, version);	
	}
}
