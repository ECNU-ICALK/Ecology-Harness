#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_DEV=0
USE_UV=0
USE_CONDA=auto
CONDA_ENV_NAME="${ECOLOGY_HARNESS_CONDA_ENV:-eh_py}"
CONDA_ENV_PYTHON="${ECOLOGY_HARNESS_CONDA_PYTHON:-3.11}"
BOOTSTRAP_MCP_RUNTIMES=1
MCP_RUNTIME_ROOT="${ECOLOGY_HARNESS_MCP_RUNTIME_ROOT:-$HOME/.ecology_harness/mcp_runtimes}"
MCP_HELPER_ENV_NAME="${ECOLOGY_HARNESS_MCP_HELPER_ENV:-mcp311}"
GIS_HELPER_ENV_NAME="${ECOLOGY_HARNESS_GIS_HELPER_ENV:-mcpgis310}"
INSTALL_OPTIONAL_PY311_MCPS=0
INSTALL_OPTIONAL_GIS_MCP=0
PROMPT_OPTIONAL_COMPONENTS=1
REFRESH_MCP_RUNTIMES=0
WARM_MCP_CACHES=0
TARGET_PYTHON=""
TARGET_ENV_LABEL=""
CONDA_ENV_PATH=""
TARGET_NODE=""
TARGET_NPM=""

log() {
  echo "==> $*"
}

warn() {
  echo "WARNING: $*" >&2
}

die() {
  echo "$*" >&2
  exit 1
}

usage() {
  cat >&2 <<EOF
Usage: bash scripts/install.sh [--with-dev] [--uv] [--conda-env NAME] [--no-conda] [--skip-mcp-runtimes] [--with-python311-mcps] [--with-gis-mcp] [--refresh-mcp-runtimes] [--warm-mcp-caches]
EOF
  exit 1
}

ensure_git_repo() {
  local url="$1"
  local dest="$2"
  if [[ -d "$dest/.git" ]]; then
    if [[ "$REFRESH_MCP_RUNTIMES" -eq 1 ]]; then
      log "Refreshing $(basename "$dest")"
      GIT_TERMINAL_PROMPT=0 git -c http.version=HTTP/1.1 -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 -C "$dest" fetch --depth 1 origin || warn "Could not refresh $(basename "$dest"); reusing existing checkout."
      git -C "$dest" reset --hard origin/HEAD >/dev/null 2>&1 || true
    else
      log "Reusing $(basename "$dest")"
    fi
    return
  fi
  rm -rf "$dest"
  log "Cloning $(basename "$dest")"
  git clone --depth 1 "$url" "$dest"
}

ensure_node_build() {
  local url="$1"
  local dest="$2"
  local npm_cmd="${TARGET_NPM:-}"
  local node_cmd="${TARGET_NODE:-}"
  ensure_git_repo "$url" "$dest"
  if [[ -z "$npm_cmd" ]]; then
    if command -v npm >/dev/null 2>&1; then
      npm_cmd="$(command -v npm)"
    fi
  fi
  if [[ -z "$node_cmd" ]]; then
    if command -v node >/dev/null 2>&1; then
      node_cmd="$(command -v node)"
    fi
  fi
  if [[ -z "$npm_cmd" || -z "$node_cmd" ]]; then
    warn "npm is unavailable; skipping build for $(basename "$dest")."
    return
  fi
  if [[ ! -f "$dest/package.json" ]]; then
    warn "Missing package.json in $dest; skipping."
    return
  fi
  log "Building $(basename "$dest")"
  pushd "$dest" >/dev/null
  "$npm_cmd" install --no-audit --no-fund
  if "$node_cmd" -e 'const p=require("./package.json");process.exit((p.scripts&&p.scripts.build)?0:1);'; then
    "$npm_cmd" run build
  else
    warn "$(basename "$dest") has no build script; leaving source checkout in place."
  fi
  popd >/dev/null
}

install_python_packages_to() {
  local python_bin="$1"
  local label="$2"
  shift 2
  if [[ $# -eq 0 ]]; then
    return
  fi
  log "Installing Python MCP helpers into $label"
  "$python_bin" -m pip install "$@"
}

install_project_package() {
  local python_bin="$1"
  local mode="$2"
  pushd "$ROOT_DIR" >/dev/null
  if [[ "$mode" == "dev" ]]; then
    if ! "$python_bin" -m pip install -e '.[dev]'; then
      warn "Editable dev install failed; retrying with a regular install. This commonly happens when the project path contains non-ASCII characters."
      "$python_bin" -m pip install '.[dev]'
    fi
  else
    if ! "$python_bin" -m pip install -e .; then
      warn "Editable install failed; retrying with a regular install. This commonly happens when the project path contains non-ASCII characters."
      "$python_bin" -m pip install .
    fi
  fi
  popd >/dev/null
}

python_supports_at_least() {
  local python_bin="$1"
  local major="$2"
  local minor="$3"
  "$python_bin" - <<PY
import sys
raise SystemExit(0 if sys.version_info >= ($major, $minor) else 1)
PY
}

ensure_helper_conda_python() {
  local env_name="$1"
  local python_spec="$2"
  local conda_bin=""
  local conda_base=""
  local env_path=""
  if ! command -v conda >/dev/null 2>&1; then
    return 1
  fi
  conda_bin="$(command -v conda)"
  conda_base="$(cd "$(dirname "$conda_bin")/.." && pwd)"
  env_path="$conda_base/envs/$env_name"
  if [[ ! -x "$env_path/bin/python" ]]; then
    log "Creating helper conda environment $env_name ($python_spec)"
    conda create -p "$env_path" -y "python=$python_spec" pip >/dev/null
  fi
  [[ -x "$env_path/bin/python" ]] || return 1
  printf '%s\n' "$env_path/bin/python"
}

create_conda_env() {
  local env_name="$1"
  local python_spec="$2"
  local conda_bin=""
  local conda_base=""
  local env_path=""
  if ! command -v conda >/dev/null 2>&1; then
    return 1
  fi
  conda_bin="$(command -v conda)"
  conda_base="$(cd "$(dirname "$conda_bin")/.." && pwd)"
  env_path="$conda_base/envs/$env_name"
  if [[ -x "$env_path/bin/python" ]]; then
    return 0
  fi
  log "Creating conda environment $env_name (python=$python_spec)"
  conda create -p "$env_path" -y "python=$python_spec" pip >/dev/null
}

prompt_yes_no() {
  local question="$1"
  local answer=""
  if [[ ! -t 0 || ! -t 1 ]]; then
    return 1
  fi
  read -r -p "$question [y/N] " answer
  case "${answer,,}" in
    y|yes)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

install_optional_python_mcp_helpers() {
  if [[ "$BOOTSTRAP_MCP_RUNTIMES" -eq 0 ]]; then
    return
  fi
  if python_supports_at_least "$TARGET_PYTHON" 3 11; then
    install_python_packages_to \
      "$TARGET_PYTHON" \
      "$TARGET_ENV_LABEL" \
      "mcp-server-baidu-maps>=0.2.4" \
      "labarchives-mcp-pol>=0.3.3"
  elif [[ "$TARGET_ENV_LABEL" == conda:* ]]; then
    local helper_python=""
    if helper_python="$(ensure_helper_conda_python "$MCP_HELPER_ENV_NAME" "3.11")"; then
      install_python_packages_to \
        "$helper_python" \
        "conda:$MCP_HELPER_ENV_NAME" \
        "mcp-server-baidu-maps>=0.2.4" \
        "labarchives-mcp-pol>=0.3.3"
    else
      warn "Could not create helper env $MCP_HELPER_ENV_NAME for Python 3.11 MCP packages; baidu-maps and labarchives will need manual setup."
    fi
  else
    warn "Skipping baidu-maps and labarchives install because they require Python 3.11+ and no conda helper environment is available."
  fi
}

install_optional_gis_mcp() {
  local target_bin=""
  local cmake_cmd=""
  if [[ "$BOOTSTRAP_MCP_RUNTIMES" -eq 0 ]]; then
    return
  fi
  target_bin="$(dirname "$TARGET_PYTHON")"
  if [[ "$TARGET_ENV_LABEL" == conda:* ]]; then
    local gis_python=""
    if gis_python="$(ensure_helper_conda_python "$GIS_HELPER_ENV_NAME" "3.10")"; then
      log "Attempting optional GIS MCP install in helper env $GIS_HELPER_ENV_NAME"
      if ! install_python_packages_to "$gis_python" "conda:$GIS_HELPER_ENV_NAME" "cmake>=3.27" "gis-mcp"; then
        warn "Optional package gis-mcp did not install cleanly in $GIS_HELPER_ENV_NAME. GIS tooling can still be installed manually later."
      fi
    else
      warn "Could not create helper env $GIS_HELPER_ENV_NAME for gis-mcp."
    fi
  else
    if [[ -x "$target_bin/cmake" ]]; then
      cmake_cmd="$target_bin/cmake"
    elif command -v cmake >/dev/null 2>&1; then
      cmake_cmd="$(command -v cmake)"
    fi
    if [[ -n "$cmake_cmd" ]]; then
      log "Attempting optional GIS MCP install"
      if ! "$TARGET_PYTHON" -m pip install "gis-mcp" >/dev/null 2>&1; then
        warn "Optional package gis-mcp did not install cleanly. GIS tooling can still be installed manually later."
      fi
    else
      warn "Skipping optional gis-mcp install because cmake is unavailable."
    fi
  fi
}

bootstrap_mcp_runtimes() {
  local target_bin
  local uvx_cmd=""
  if [[ "$BOOTSTRAP_MCP_RUNTIMES" -eq 0 ]]; then
    return
  fi

  log "Bootstrapping MCP runtime prerequisites"
  mkdir -p "$MCP_RUNTIME_ROOT"
  target_bin="$(dirname "$TARGET_PYTHON")"
  TARGET_NODE=""
  TARGET_NPM=""

  if [[ "$TARGET_ENV_LABEL" == conda:* && -n "$CONDA_ENV_PATH" ]]; then
    if [[ -x "$CONDA_ENV_PATH/bin/node" ]]; then
      TARGET_NODE="$CONDA_ENV_PATH/bin/node"
    fi
    if [[ -x "$CONDA_ENV_PATH/bin/npm" ]]; then
      TARGET_NPM="$CONDA_ENV_PATH/bin/npm"
    fi
    if [[ -z "$TARGET_NODE" && -x "$(command -v node 2>/dev/null || true)" ]]; then
      TARGET_NODE="$(command -v node)"
    fi
    if [[ -z "$TARGET_NPM" && -x "$(command -v npm 2>/dev/null || true)" ]]; then
      TARGET_NPM="$(command -v npm)"
    fi
    if [[ -z "$TARGET_NODE" || -z "$TARGET_NPM" ]]; then
      log "Ensuring nodejs is available in $CONDA_ENV_NAME"
      conda install -p "$CONDA_ENV_PATH" -y -c conda-forge nodejs || warn "Failed to install nodejs via conda; continuing with existing tooling."
      hash -r || true
      if [[ -x "$CONDA_ENV_PATH/bin/node" ]]; then
        TARGET_NODE="$CONDA_ENV_PATH/bin/node"
      fi
      if [[ -x "$CONDA_ENV_PATH/bin/npm" ]]; then
        TARGET_NPM="$CONDA_ENV_PATH/bin/npm"
      fi
    fi
  fi

  install_python_packages_to \
    "$TARGET_PYTHON" \
    "$TARGET_ENV_LABEL" \
    "uv>=0.8.15" \
    "mcp-simple-pubmed>=0.1.16"

  ensure_node_build "https://github.com/tyson-swetnam/gbif-mcp.git" "$MCP_RUNTIME_ROOT/gbif-mcp"
  ensure_node_build "https://github.com/influxdata/influxdb3_mcp_server.git" "$MCP_RUNTIME_ROOT/influxdb3_mcp_server"
  ensure_node_build "https://github.com/Augmented-Nature/NCBI-Datasets-MCP-Server.git" "$MCP_RUNTIME_ROOT/ncbi-datasets-server"
  ensure_node_build "https://github.com/Augmented-Nature/PubChem-MCP-Server.git" "$MCP_RUNTIME_ROOT/pubchem-server"
  ensure_git_repo "https://github.com/bio-mcp/bio-mcp-blast.git" "$MCP_RUNTIME_ROOT/bio-mcp-blast"

  if [[ -d "$MCP_RUNTIME_ROOT/bio-mcp-blast" ]]; then
    log "Installing Bio-MCP BLAST Python dependencies"
    if ! "$TARGET_PYTHON" -m pip install -e "$MCP_RUNTIME_ROOT/bio-mcp-blast" >/dev/null 2>&1; then
      warn "Could not install editable Bio-MCP BLAST package; runtime source checkout is still available at $MCP_RUNTIME_ROOT/bio-mcp-blast."
    fi
  fi

  if [[ -x "$target_bin/uvx" ]]; then
    uvx_cmd="$target_bin/uvx"
  elif command -v uvx >/dev/null 2>&1; then
    uvx_cmd="$(command -v uvx)"
  fi

  if [[ -n "$uvx_cmd" && "$WARM_MCP_CACHES" -eq 1 ]]; then
    log "Warming uvx-based MCP entrypoints"
    "$uvx_cmd" --from "git+https://github.com/wayfinder-foundry/stac-mcp" stac-mcp --help >/dev/null 2>&1 || warn "stac-mcp cache warmup failed; it can still resolve on first use."
    "$uvx_cmd" jupyter-mcp-server@latest --help >/dev/null 2>&1 || warn "jupyter-mcp-server cache warmup failed; it can still resolve on first use."
    "$uvx_cmd" unit-converter-mcp --help >/dev/null 2>&1 || warn "unit-converter-mcp cache warmup failed; it can still resolve on first use."
    "$uvx_cmd" swiss-environment-mcp --help >/dev/null 2>&1 || warn "swiss-environment-mcp cache warmup failed; it can still resolve on first use."
    "$uvx_cmd" wsl-envidat-mcp --help >/dev/null 2>&1 || warn "wsl-envidat-mcp cache warmup failed; it can still resolve on first use."
    "$uvx_cmd" data-commons-search --help >/dev/null 2>&1 || warn "data-commons-search cache warmup failed; it can still resolve on first use."
  elif [[ -n "$uvx_cmd" ]]; then
    log "Skipping uvx cache warmup (use --warm-mcp-caches to prefetch uvx-backed MCP servers)"
  else
    warn "uvx is unavailable after bootstrap; uv-backed MCP servers will resolve only after uv is installed."
  fi
}

resolve_conda_env_python() {
  local env_name="$1"
  local conda_bin=""
  local conda_base=""
  local env_path=""
  if ! command -v conda >/dev/null 2>&1; then
    return 1
  fi
  conda_bin="$(command -v conda)"
  conda_base="$(cd "$(dirname "$conda_bin")/.." && pwd)"
  if [[ "${CONDA_DEFAULT_ENV:-}" == "$env_name" ]]; then
    TARGET_PYTHON="$(command -v python)"
    TARGET_ENV_LABEL="conda:$env_name"
    CONDA_ENV_PATH="$(cd "$(dirname "$TARGET_PYTHON")/.." && pwd)"
    return 0
  fi
  env_path="$conda_base/envs/$env_name"
  if [[ ! -x "$env_path/bin/python" ]]; then
    return 1
  fi
  TARGET_PYTHON="$env_path/bin/python"
  TARGET_ENV_LABEL="conda:$env_name"
  CONDA_ENV_PATH="$env_path"
  return 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-dev)
      WITH_DEV=1
      ;;
    --uv)
      USE_UV=1
      ;;
    --conda-env)
      shift
      [[ $# -gt 0 ]] || usage
      CONDA_ENV_NAME="$1"
      USE_CONDA=1
      ;;
    --conda-env=*)
      CONDA_ENV_NAME="${1#*=}"
      USE_CONDA=1
      ;;
    --no-conda)
      USE_CONDA=0
      ;;
    --skip-mcp-runtimes)
      BOOTSTRAP_MCP_RUNTIMES=0
      PROMPT_OPTIONAL_COMPONENTS=0
      ;;
    --with-python311-mcps)
      INSTALL_OPTIONAL_PY311_MCPS=1
      PROMPT_OPTIONAL_COMPONENTS=0
      ;;
    --with-gis-mcp)
      INSTALL_OPTIONAL_GIS_MCP=1
      PROMPT_OPTIONAL_COMPONENTS=0
      ;;
    --refresh-mcp-runtimes)
      REFRESH_MCP_RUNTIMES=1
      ;;
    --warm-mcp-caches)
      WARM_MCP_CACHES=1
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  die "python3 is required but was not found in PATH."
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit("Python 3.9+ is required.")
PY

log "Preparing Ecology Harness installation"
echo "    root: $ROOT_DIR"

if [[ "$USE_CONDA" != "0" && "$USE_UV" -eq 0 ]]; then
  if resolve_conda_env_python "$CONDA_ENV_NAME"; then
    log "Using existing conda environment $CONDA_ENV_NAME"
  elif [[ "$USE_CONDA" == "1" || "$CONDA_ENV_NAME" == "eh_py" ]]; then
    if ! command -v conda >/dev/null 2>&1; then
      die "Conda environment '$CONDA_ENV_NAME' was requested but conda is not available."
    fi
    create_conda_env "$CONDA_ENV_NAME" "$CONDA_ENV_PYTHON"
    resolve_conda_env_python "$CONDA_ENV_NAME" || die "Failed to resolve conda environment '$CONDA_ENV_NAME' after creation."
    log "Using newly created conda environment $CONDA_ENV_NAME"
  elif [[ "$USE_CONDA" == "1" ]]; then
    die "Requested conda environment '$CONDA_ENV_NAME' was not found."
  fi
fi

if [[ -n "$TARGET_PYTHON" ]]; then
  log "Installing package into $TARGET_ENV_LABEL"
  "$TARGET_PYTHON" -m pip install --upgrade pip setuptools wheel
  if [[ "$WITH_DEV" -eq 1 ]]; then
    install_project_package "$TARGET_PYTHON" "dev"
  else
    install_project_package "$TARGET_PYTHON" "default"
  fi
elif [[ "$USE_UV" -eq 1 ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    die "uv was requested but is not installed."
  fi
  log "Installing with uv"
  if [[ "$WITH_DEV" -eq 1 ]]; then
    uv sync --directory "$ROOT_DIR" --extra dev
  else
    uv sync --directory "$ROOT_DIR"
  fi
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    TARGET_PYTHON="$ROOT_DIR/.venv/bin/python"
    TARGET_ENV_LABEL="uv:$ROOT_DIR/.venv"
  else
    warn "uv completed but $ROOT_DIR/.venv/bin/python was not found; skipping MCP runtime bootstrap."
    BOOTSTRAP_MCP_RUNTIMES=0
  fi
else
  log "Creating virtual environment"
  python3 -m venv "$ROOT_DIR/.venv"
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"
  TARGET_PYTHON="$(command -v python3)"
  TARGET_ENV_LABEL="venv:$ROOT_DIR/.venv"

  log "Upgrading packaging tools"
  python3 -m pip install --upgrade pip setuptools wheel

  log "Installing package"
  if [[ "$WITH_DEV" -eq 1 ]]; then
    install_project_package "$TARGET_PYTHON" "dev"
  else
    install_project_package "$TARGET_PYTHON" "default"
  fi
fi

mkdir -p "$HOME/.ecology_harness/memory" "$HOME/.ecology_harness/skills" "$HOME/.ecology_harness/agents"
bootstrap_mcp_runtimes

if [[ "$INSTALL_OPTIONAL_PY311_MCPS" -eq 1 ]]; then
  install_optional_python_mcp_helpers
fi
if [[ "$INSTALL_OPTIONAL_GIS_MCP" -eq 1 ]]; then
  install_optional_gis_mcp
fi
if [[ "$PROMPT_OPTIONAL_COMPONENTS" -eq 1 && "$BOOTSTRAP_MCP_RUNTIMES" -eq 1 ]]; then
  if prompt_yes_no "Install optional baidu-maps and labarchives MCP helpers?"; then
    install_optional_python_mcp_helpers
  fi
  if prompt_yes_no "Install optional GIS MCP stack (gis-mcp)?"; then
    install_optional_gis_mcp
  fi
fi

echo
echo "Ecology Harness is ready."
echo
echo "Next steps:"
if [[ "$USE_UV" -eq 1 && -z "$TARGET_PYTHON" ]]; then
  echo "  uv run --directory \"$ROOT_DIR\" eh --help"
  echo "  uv run --directory \"$ROOT_DIR\" eh -p '/tool Read {\"path\":\"README.md\"}'"
  echo "  uv run --directory \"$ROOT_DIR\" eh --repl"
elif [[ "$TARGET_ENV_LABEL" == conda:* ]]; then
  echo "  source activate \"$CONDA_ENV_NAME\""
  echo "  eh doctor"
  echo "  eh mcp"
  echo "  eh --help"
  echo
  echo "Optional add-ons:"
  echo "  bash scripts/install.sh --conda-env \"$CONDA_ENV_NAME\" --with-python311-mcps"
  echo "  bash scripts/install.sh --conda-env \"$CONDA_ENV_NAME\" --with-gis-mcp"
else
  echo "  source \"$ROOT_DIR/.venv/bin/activate\""
  echo "  eh --help"
  echo "  eh -p '/tool Read {\"path\":\"README.md\"}'"
  echo "  eh --repl"
fi
