#!/usr/bin/env bash
# Audita los paquetes de la aplicación sin cambiar sus dependencias.
set -euo pipefail

# GitHub proporciona RUNNER_TEMP para guardar herramientas temporales.
AUDIT_ENV="$RUNNER_TEMP/pip-audit"
python -m venv "$AUDIT_ENV"
"$AUDIT_ENV/bin/python" -m pip install pip-audit==2.10.1

# Esta ruta corresponde al Python de la aplicación, no al del auditor.
APP_PACKAGES=$(python -c 'import sysconfig; print(sysconfig.get_path("purelib"))')

# Solo se permiten las tres excepciones explicadas en docs/dependency-audit.md.
"$AUDIT_ENV/bin/python" -m pip_audit \
  --path "$APP_PACKAGES" --skip-editable \
  --ignore-vuln CVE-2025-47278 \
  --ignore-vuln CVE-2026-27205 \
  --ignore-vuln CVE-2026-28684 \
  --format json --output pip-audit.json
