FROM rust:1.71

RUN apt-get update && \
    apt-get install --assume-yes --no-install-recommends gcc-mingw-w64 libz-mingw-w64-dev

RUN rustup target add x86_64-pc-windows-gnu && \
    rustup toolchain install stable-x86_64-pc-windows-gnu