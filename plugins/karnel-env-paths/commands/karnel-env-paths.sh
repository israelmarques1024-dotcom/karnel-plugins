#!/usr/bin/env bash

karnel-env-paths_main() {
  if [[ $# -ne 0 ]]; then
    printf 'Usage: karnel-env-paths\n' >&2
    return 2
  fi

  printf 'Karnel environment\n'
  printf 'version: %s\n' "${KARNEL_VERSION:-unknown}"
  printf 'config: %s\n' "${KARNEL_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/karnel}"
  printf 'data: %s\n' "${KARNEL_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/karnel-data}"
  printf 'cache: %s\n' "${KARNEL_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/karnel}"
  printf 'plugins: %s\n' "${PLUGINS_DIR:-${KARNEL_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/karnel-data}/plugins}"
  printf 'prefix: %s\n' "${PREFIX:-unknown}"
}
