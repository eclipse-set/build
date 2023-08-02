# rootfiles-maven-plugin

## The Issue

When deploying an OSGi Feature with rootfiles to a maven repository (e.g. Github Packages), `root`-files are deployed separately (as another maven artifact with classifier `root` and type `zip`). When importing the feature within a target platform (via the m2e maven target support), the root files are not being downloaded.

## The Workaround

This minimal maven plugin allows to download the root files for a deployed root feature. The downloaded files can then be added to a new feature as root files

### Usage

The following example downloads the latest Eclipse SET feature root files into the local `rootdir_set` folder.

```xml
<plugin>
    <groupId>org.eclipse.set</groupId>
	<artifactId>rootfiles-maven-plugin</artifactId>
	<version>1.0.0</version>
	<executions>
	    <execution>
		    <id>fetch-set-feature</id>
			<goals>
			    <goal>fetch</goal>
			</goals>
			<configuration>
                <serverId>github-set</serverId>
                <serverUrl>https://maven.pkg.github.com/eclipse-set/set</serverUrl>
                <groupId>org.eclipse.set</groupId>
                <artifactId>org.eclipse.set.feature</artifactId>
                <version>2.1.0-SNAPSHOT</version>
                <outPath>${basedir}/rootdir_set</outPath>
            </configuration>
	    </execution>
    <executions>
</plugin>
```

### Parameters

- serverId: The maven server id to use for retrieving the artifact.
- serverUrl: The maven server url to use for retrieving the artifact.
- groupId/artifactId/version: The GAV for the artifact to fetch.
- outPath: Output directory for extracted files
