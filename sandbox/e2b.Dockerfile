# Use Kali Linux as the base image
FROM kalilinux/kali-rolling

# Set environment variables to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Update and install a core set of CTF tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    netcat-traditional \
    nmap \
    sqlmap \
    nikto \
    gobuster \
    dirb \
    python3 \
    python3-pip \
    python3-venv \
    whois \
    dnsutils \
    net-tools \
    iputils-ping \
    bsdmainutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Fix for gobuster/dirb: they often need wordlists. 
# We'll install a small set or point them to common paths.
RUN apt-get update && apt-get install -y wordlists && apt-get clean

# Set the working directory
WORKDIR /home/ctf

# Optional: Add a user for safety, though many Kali tools prefer root
# For E2B sandboxes, running as root is often okay as it's isolated.
