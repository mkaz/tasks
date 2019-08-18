#!/bin/bash

# Build Script for creating multiple architecture releases

# Requires:
# go get github.com/mitchellh/gox

## get version from self to include in file names
go build
VERSION=`task --version | sed -e 's/Task v//'`

echo "Building $VERSION"
gox -osarch="linux/amd64 darwin/amd64 windows/amd64" -output "{{.Dir}}-$VERSION-{{.OS}}/{{.Dir}}"

for arch in linux darwin windows; do
    tar cf task-$VERSION-$arch.tar task-$VERSION-$arch
    gzip task-$VERSION-$arch.tar
    rm -rf task-$VERSION-$arch
done

