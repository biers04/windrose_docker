FROM scottyhardy/docker-wine:stable

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends jq python3 tini xvfb \
    && rm -rf /var/lib/apt/lists/*

ENV WINEPREFIX=/wine \
    WINEARCH=win64 \
    DISPLAY=:0

WORKDIR /srv/windrose

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/apply_managed_config.py /usr/local/bin/apply_managed_config.py

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/apply_managed_config.py

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
