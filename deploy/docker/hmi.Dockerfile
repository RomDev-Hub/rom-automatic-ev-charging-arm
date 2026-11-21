# Image ghcr.io/romdev-hub/ev-arm-hmi (REQ-DEP-003): build operator-ui bằng pnpm ra file tĩnh, rồi Caddy phục vụ qua HTTPS và chuyển /api tới service core.
# Build từ gốc repo: docker build -f deploy/docker/hmi.Dockerfile --build-arg VERSION=<X.Y.Z> --build-arg REVISION=<commit> .

FROM node:26.13.1-trixie-slim@sha256:e6bedef217677b276c591795e169840edd9096dbf13f29df8ef8d1856b8820bc AS build
# Cùng bản pnpm với devEngines.packageManager trong package.json (ADR 0008).
RUN npm install -g pnpm@12.18.0
WORKDIR /src
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY operator-ui/package.json operator-ui/
RUN pnpm install --frozen-lockfile --filter operator-ui
# Chép từng phần nguồn của bản build, để node_modules của máy build không vào image.
COPY operator-ui/index.html operator-ui/vite.config.ts operator-ui/tsconfig.json operator-ui/
COPY operator-ui/src operator-ui/src
# Chuỗi hiển thị của operator-ui lấy từ hai file locale của robot-core (REQ-I18N-001).
COPY robot-core/src/robot_core/locales robot-core/src/robot_core/locales
RUN pnpm --filter operator-ui run build

FROM caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0
ARG VERSION=0.0.0+local
ARG REVISION=unknown
# Image caddy đặt sẵn nhãn OCI title, description, url, documentation, source và vendor của chính Caddy; ghi đè cả sáu bằng thông tin của dự án này.
LABEL org.opencontainers.image.title="ev-arm-hmi" \
      org.opencontainers.image.description="Operator HMI of the automatic EV charging arm: operator-ui served over HTTPS by Caddy, which proxies REST and WSS to core" \
      org.opencontainers.image.url="https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm" \
      org.opencontainers.image.documentation="https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm/tree/main/docs" \
      org.opencontainers.image.source="https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm" \
      org.opencontainers.image.vendor="Mr.Ròm" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"
COPY deploy/docker/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/operator-ui/dist /srv
# User không phải root, cùng UID và GID với image core. Rootfs chạy chỉ đọc; /data và /config của Caddy là tmpfs mà UID này ghi được, ví dụ `--tmpfs /data:uid=10001,gid=10001` (ADR 0007).
USER 10001:10001
EXPOSE 8443
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
