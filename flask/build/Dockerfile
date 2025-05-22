# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.13.2 AS builder

WORKDIR /code

ENV PYTHONUNBUFFERED=1

ADD setup.sh /
RUN chmod +x /setup.sh
CMD ["/setup.sh"]

FROM builder as dev-envs

RUN <<EOF
apt update
apt install git bash
EOF

RUN <<EOF
groupadd docker
useradd -m -s /bin/bash -G docker vscode
EOF

#addgroup -S docker
#adduser -S --shell /bin/bash --ingroup docker vscode

# install Docker tools (cli, buildx, compose)
COPY --from=gloursdocker/docker / /