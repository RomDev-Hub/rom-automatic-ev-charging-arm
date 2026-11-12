# Image ghcr.io/romdev-hub/ev-arm-core, chỉ dùng CPU (REQ-DEP-001, REQ-DEP-002): target runtime chạy trên thiết bị, target dev chạy test của robot-core ở mức 2.
# Build từ gốc repo: docker build -f deploy/docker/core.Dockerfile --target runtime --build-arg VERSION=<X.Y.Z> --build-arg REVISION=<commit> .

# Phiên bản SemVer lấy từ tag Git; build tại máy không truyền thì nhận giá trị này, không phải bản phát hành nào (REQ-DEP-006).
ARG VERSION=0.0.0+local

FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

FROM python:3.14.10-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS python
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

FROM python AS builder
# Công cụ build ur_rtde từ sdist: C/C++, CMake, Boost system/thread/program_options, và git để CMake kéo pybind11 từ GitHub (ADR 0008).
# Gói apt không ghim phiên bản (DL3008): kho Debian chỉ phục vụ bản hiện hành của mỗi gói, nên bản đã ghim biến mất sau lần cập nhật kế tiếp và build hỏng; image gốc đã ghim theo digest.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake g++ gcc git libboost-program-options-dev libboost-system-dev libboost-thread-dev make \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /src/robot-core
# Cài dependency trước project, nên đổi mã nguồn không làm build lại ur_rtde; cache của uv giữ wheel đã build qua các lần build.
COPY robot-core/pyproject.toml robot-core/uv.lock robot-core/.python-version ./
# setup.py của ur_rtde gọi `cmake --build` không kèm -j; biến này đặt số job song song.
ARG BUILD_JOBS=4
RUN --mount=type=cache,target=/root/.cache/uv \
    CMAKE_BUILD_PARALLEL_LEVEL=${BUILD_JOBS} uv sync --frozen --no-dev --no-editable --no-install-project
COPY robot-core/LICENSE ./
COPY robot-core/src ./src
# Không có thư mục .git trong context, nên hatch-vcs nhận phiên bản qua biến pretend-version của setuptools-scm.
# Cũng vì thế mà khoá cache của uv cho robot-core (pyproject.toml, commit Git) không đổi khi mã đổi; --reinstall-package buộc build lại từ src.
ARG VERSION
RUN --mount=type=cache,target=/root/.cache/uv \
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ROBOT_CORE=${VERSION} uv sync --frozen --no-dev --no-editable --reinstall-package robot-core

FROM builder AS dev-venv
ARG VERSION
RUN --mount=type=cache,target=/root/.cache/uv \
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ROBOT_CORE=${VERSION} uv sync --frozen --no-editable --group dev

FROM python AS runtime
# Thư viện dùng chung mà các wheel cần lúc chạy: Boost.Thread cho ur_rtde, libgomp cho pin (ADR 0008).
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends libboost-thread1.83.0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
# User cố định UID 10001, GID 10001 (ADR 0007). Thư mục mount tạo sẵn thuộc user này, vì volume mới chỉ nhận chủ sở hữu từ image khi còn rỗng.
RUN groupadd --gid 10001 ev-arm \
    && useradd --uid 10001 --gid ev-arm --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin ev-arm \
    && install -d -o ev-arm -g ev-arm -m 0750 /var/lib/ev-arm/config /var/lib/ev-arm/state /var/lib/ev-arm/recordings /var/lib/ev-arm/harvest /var/lib/ev-arm/models
COPY --from=builder /opt/venv /opt/venv
# Nghe mọi địa chỉ trong container; core không mở cổng nào ra LAN (REQ-DEP-014), nên image không khai EXPOSE.
ENV EV_ARM_HOST=0.0.0.0
USER 10001:10001
ARG VERSION
ARG REVISION=unknown
LABEL org.opencontainers.image.title=ev-arm-core \
      org.opencontainers.image.description="Core service of the automatic EV charging arm (robot-core): REST and WSS API, mission, motion supervision and kinematics, CPU only" \
      org.opencontainers.image.url=https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm \
      org.opencontainers.image.documentation=https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm/tree/main/docs \
      org.opencontainers.image.source=https://github.com/RomDev-Hub/rom-automatic-ev-charging-arm \
      org.opencontainers.image.vendor=Mr.Ròm \
      org.opencontainers.image.version=${VERSION} \
      org.opencontainers.image.revision=${REVISION} \
      org.opencontainers.image.licenses=AGPL-3.0-or-later
CMD ["robot-core", "serve"]

# Runtime cộng nhóm dependency dev và bộ test; test chạy trên đúng thư viện hệ thống của image runtime.
FROM runtime AS dev
COPY --from=dev-venv /opt/venv /opt/venv
WORKDIR /app/robot-core
COPY contracts /app/contracts
COPY robot-core/pyproject.toml ./
COPY robot-core/tests ./tests
# Thư mục làm việc chỉ đọc với user chạy test, nên tắt cache của pytest.
ENV PYTEST_ADDOPTS="-p no:cacheprovider"
