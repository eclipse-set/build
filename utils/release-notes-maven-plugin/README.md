# release-note-maven-plugin
## The Issue
## The Workaround
This maven plugin transform RELEAS_NOTE.md to asciidoc file, that use for show release note in SET application

### Usage
```xml
<plugin>
    <groupId>org.eclipse.set</groupId>
	<artifactId>release-note-maven-plugin</artifactId>
	<version>1.0.0</version>
	<executions>
	    <execution>
		    <id>transform-release-note</id>
        <configuration>
                <notesPath>../RELEASE_NOTE.md</notesPath>
                <outDir>../web/news/content/</outdir>
            </configuration>
	    </execution>
    <executions>
</plugin>
```

### Parameters
- notesPath: path to RELEASE_NOTE.md
- outDir: directory for asciidoc file