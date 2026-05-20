#!/usr/bin/env bash

set -euo pipefail

DEVICE_ID="${MOMAX_DEVICE_ID:-MOMAX BS6}"
AUDIO_OUTPUT_NAME="${MOMAX_AUDIO_OUTPUT_NAME:-$DEVICE_ID}"
SET_AUDIO_OUTPUT="${MOMAX_SET_AUDIO_OUTPUT:-1}"
BLUEUTIL="${BLUEUTIL_BIN:-}"

usage() {
  cat <<'EOF'
Usage:
  momax-bs6.sh connect
  momax-bs6.sh disconnect
  momax-bs6.sh toggle
  momax-bs6.sh status

Environment variables:
  MOMAX_DEVICE_ID          Bluetooth device name or address. Default: MOMAX BS6
  MOMAX_AUDIO_OUTPUT_NAME  macOS audio output name. Default: same as MOMAX_DEVICE_ID
  MOMAX_SET_AUDIO_OUTPUT   Set output via SwitchAudioSource after connect. Default: 1
  BLUEUTIL_BIN             blueutil path override.

Examples:
  ./momax-bs6.sh toggle
  MOMAX_DEVICE_ID="xx-xx-xx-xx-xx-xx" ./momax-bs6.sh connect
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

find_blueutil() {
  if [[ -n "$BLUEUTIL" ]]; then
    [[ -x "$BLUEUTIL" ]] || die "BLUEUTIL_BIN is not executable: $BLUEUTIL"
    return
  fi

  if command -v blueutil >/dev/null 2>&1; then
    BLUEUTIL="$(command -v blueutil)"
    return
  fi

  for candidate in /opt/homebrew/bin/blueutil /usr/local/bin/blueutil; do
    if [[ -x "$candidate" ]]; then
      BLUEUTIL="$candidate"
      return
    fi
  done

  die "blueutil is required. Install it with: brew install blueutil"
}

run_blueutil() {
  local output status

  set +e
  output="$("$BLUEUTIL" "$@" 2>&1)"
  status=$?
  set -e

  if [[ $status -eq 134 ]] || grep -qi 'Bluetooth API' <<<"$output"; then
    cat >&2 <<'EOF'
Error: blueutil has no Bluetooth permission.

Open:
  System Settings > Privacy & Security > Bluetooth

Then enable Bluetooth access for the app that runs this script
(Terminal, iTerm, Raycast, Shortcuts, or Codex).
EOF
    exit "$status"
  fi

  if [[ $status -ne 0 ]]; then
    printf '%s\n' "$output" >&2
    return "$status"
  fi

  printf '%s\n' "$output"
}

ensure_power_on() {
  local state
  state="$(run_blueutil --power | tr -d '[:space:]')" || exit $?

  if [[ "$state" != "1" ]]; then
    printf 'Bluetooth is off. Turning it on...\n'
    run_blueutil --power 1 >/dev/null
    sleep 1
  fi
}

connection_state() {
  local state
  state="$(run_blueutil --is-connected "$DEVICE_ID" | tr -d '[:space:]')" || return $?

  case "$state" in
    0|1)
      printf '%s\n' "$state"
      ;;
    *)
      die "unexpected connection state for $DEVICE_ID: $state"
      ;;
  esac
}

switch_audio_output() {
  local switch_audio_source

  [[ "$SET_AUDIO_OUTPUT" == "1" ]] || return 0

  if command -v SwitchAudioSource >/dev/null 2>&1; then
    switch_audio_source="$(command -v SwitchAudioSource)"
  elif [[ -x /opt/homebrew/bin/SwitchAudioSource ]]; then
    switch_audio_source="/opt/homebrew/bin/SwitchAudioSource"
  elif [[ -x /usr/local/bin/SwitchAudioSource ]]; then
    switch_audio_source="/usr/local/bin/SwitchAudioSource"
  else
    return 0
  fi

  "$switch_audio_source" -s "$AUDIO_OUTPUT_NAME" -t output >/dev/null 2>&1 || true
}

connect_device() {
  local state

  ensure_power_on

  state="$(connection_state)" || exit $?
  if [[ "$state" == "1" ]]; then
    printf '%s is already connected.\n' "$DEVICE_ID"
    switch_audio_output
    return 0
  fi

  printf 'Connecting %s...\n' "$DEVICE_ID"
  if ! run_blueutil --connect "$DEVICE_ID" >/dev/null; then
    cat >&2 <<EOF
Failed to connect $DEVICE_ID.

If the speaker is already connected to your iPhone, disconnect it there first,
or press the speaker Bluetooth button to make it available, then run again.
EOF
    exit 75
  fi
  run_blueutil --wait-connect "$DEVICE_ID" 8 >/dev/null || true

  state="$(connection_state)" || exit $?
  if [[ "$state" == "1" ]]; then
    switch_audio_output
    printf '%s connected.\n' "$DEVICE_ID"
    return 0
  fi

  cat >&2 <<EOF
Failed to connect $DEVICE_ID.

If the speaker is already connected to your iPhone, disconnect it there first,
or press the speaker Bluetooth button to make it available, then run again.
EOF
  exit 75
}

disconnect_device() {
  local state

  state="$(connection_state)" || exit $?
  if [[ "$state" == "0" ]]; then
    printf '%s is already disconnected.\n' "$DEVICE_ID"
    return 0
  fi

  printf 'Disconnecting %s...\n' "$DEVICE_ID"
  run_blueutil --disconnect "$DEVICE_ID" >/dev/null
  run_blueutil --wait-disconnect "$DEVICE_ID" 5 >/dev/null || true

  state="$(connection_state)" || exit $?
  if [[ "$state" == "1" ]]; then
    die "failed to disconnect $DEVICE_ID"
  fi

  printf '%s disconnected.\n' "$DEVICE_ID"
}

status_device() {
  local state

  state="$(connection_state)" || exit $?
  if [[ "$state" == "1" ]]; then
    printf '%s is connected.\n' "$DEVICE_ID"
  else
    printf '%s is disconnected.\n' "$DEVICE_ID"
  fi
}

main() {
  local action="${1:-toggle}"
  local state

  case "$action" in
    -h|--help|help)
      usage
      ;;
    connect)
      find_blueutil
      connect_device
      ;;
    disconnect)
      find_blueutil
      disconnect_device
      ;;
    toggle)
      find_blueutil
      state="$(connection_state)" || exit $?
      if [[ "$state" == "1" ]]; then
        disconnect_device
      else
        connect_device
      fi
      ;;
    status)
      find_blueutil
      status_device
      ;;
    *)
      usage >&2
      exit 64
      ;;
  esac
}

main "$@"
