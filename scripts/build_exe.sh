#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
frontend_dir="$repo_root/frontend"
backend_dir="$repo_root/backend"
python_exe="$backend_dir/venv/bin/python"

if [[ ! -d "$frontend_dir" ]]; then
  echo "Frontend-Verzeichnis nicht gefunden: $frontend_dir" >&2
  exit 1
fi

if [[ ! -d "$backend_dir" ]]; then
  echo "Backend-Verzeichnis nicht gefunden: $backend_dir" >&2
  exit 1
fi

if [[ ! -x "$python_exe" ]]; then
  echo "Python-Venv nicht gefunden: $python_exe" >&2
  exit 1
fi

(
  cd "$frontend_dir"
  npm run build
)

(
  cd "$backend_dir"
  "$python_exe" -m PyInstaller --noconfirm admin_gui.spec
)

artifact_path="$backend_dir/dist/easyWahl-v1.2.0"
if [[ -f "${artifact_path}.exe" ]]; then
  artifact_path="${artifact_path}.exe"
fi

echo "Build abgeschlossen: $artifact_path"
