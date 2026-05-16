FROM quay.io/pypa/manylinux2014_x86_64

# Install build dependencies
RUN yum -y install python3-pip python3-devel && \
    pip3 install --upgrade pip setuptools wheel cibuildwheel

# Set workdir
WORKDIR /io

# Build wheels
CMD ["cibuildwheel", "--output-dir", "dist"]
