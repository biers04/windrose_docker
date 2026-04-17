FROM scottyhardy/docker-wine:stable

USER root

RUN dpkg --add-architecture i386

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl jq lib32gcc-s1 lib32stdc++6 python3 rsync tini xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/steamcmd \
    && curl -fsSL https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz -o /tmp/steamcmd_linux.tar.gz \
    && tar -xzf /tmp/steamcmd_linux.tar.gz -C /opt/steamcmd \
    && rm -f /tmp/steamcmd_linux.tar.gz

ENV WINEPREFIX=/wine \
    WINEARCH=win64 \
    DISPLAY=:0 \
    STEAMCMD_DIR=/opt/steamcmd

WORKDIR /srv/windrose

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/apply_managed_config.py /usr/local/bin/apply_managed_config.py
COPY docker/update-source.sh /usr/local/bin/update-source.sh

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/apply_managed_config.py /usr/local/bin/update-source.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
