#!/usr/bin/env bash
set -euo pipefail

# Installiert die STEP-BY-STEP Desktop-Verknüpfung samt Icon für den aktuellen Nutzer.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

ICON_SOURCE="${REPO_ROOT}/assets/step-by-step-icon.svg"
DESKTOP_TEMPLATE="${REPO_ROOT}/packaging/step-by-step.desktop"

if [[ ! -f "${ICON_SOURCE}" ]]; then
  echo "[Desktop-Setup] Icon-Datei fehlt: ${ICON_SOURCE}" >&2
  exit 1
fi

if [[ ! -f "${DESKTOP_TEMPLATE}" ]]; then
  echo "[Desktop-Setup] Desktop-Template fehlt: ${DESKTOP_TEMPLATE}" >&2
  exit 1
fi

XDG_DATA_HOME=${XDG_DATA_HOME:-"${HOME}/.local/share"}
ICON_DIR="${XDG_DATA_HOME}/icons/hicolor/scalable/apps"
DESKTOP_DIR="${XDG_DATA_HOME}/applications"
LAUNCHER_DIR="${HOME}/.local/bin"

mkdir -p "${ICON_DIR}" "${DESKTOP_DIR}" "${LAUNCHER_DIR}"

ICON_TARGET="${ICON_DIR}/step-by-step.svg"
DESKTOP_TARGET="${DESKTOP_DIR}/step-by-step.desktop"
LAUNCHER_TARGET="${LAUNCHER_DIR}/step-by-step-launcher"

install -m 644 "${ICON_SOURCE}" "${ICON_TARGET}"

cat > "${LAUNCHER_TARGET}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "${REPO_ROOT}"
exec ./bootstrap.sh "\$@"
EOF
chmod +x "${LAUNCHER_TARGET}"

sed \
  -e "s|{{LAUNCHER}}|${LAUNCHER_TARGET}|g" \
  "${DESKTOP_TEMPLATE}" > "${DESKTOP_TARGET}"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${DESKTOP_DIR}" || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache "${ICON_DIR%/icons/hicolor/scalable/apps}/icons" >/dev/null 2>&1 || true
fi

echo "[Desktop-Setup] Verknüpfung installiert: ${DESKTOP_TARGET}"
echo "[Desktop-Setup] Icon kopiert nach: ${ICON_TARGET}"
echo "[Desktop-Setup] Starter-Skript: ${LAUNCHER_TARGET}"

