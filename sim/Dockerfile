FROM espressif/idf:v5.4

# Mark the firmware as a safe include directory for git
RUN git config --global --add safe.directory "*"

# Add Pillow to the build environment
RUN bash -c "apt update && apt install -y python3-pillow && apt clean"

ADD qemu-xtensa-softmmu-esp_develop_9.2.2_20250228-x86_64-linux-gnu.tar.xz /

# Copy the build script in and define that as the entrypoint
COPY build.sh /
ENTRYPOINT ["/opt/esp/entrypoint.sh", "/build.sh"]
