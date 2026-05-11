#!/bin/zsh
set -euo pipefail

usage() {
  cat <<'EOF'
Enable Doubao IME hidden global ASR shortcut switch.

Usage:
  ./enable-doubao-global-asr.sh
  ./enable-doubao-global-asr.sh --help

What it does:
  Sends Doubao IME's internal distributed notification to request enabling
  the hidden isGloableASRShortcutEnable setting.

What it does not do:
  - It does not set the voice shortcut key.
  - It does not switch input sources.
  - It does not restore WeType/WeChat IME after voice input.
  - It does not grant macOS Accessibility or Microphone permissions.
EOF
}

case "${1:-}" in
  -h|--help|help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if ! /usr/bin/pgrep -x DoubaoIme >/dev/null 2>&1; then
  printf 'Warning: DoubaoIme process is not running. Open or restart Doubao IME, then run this script again if the shortcut still does not work.\n' >&2
fi

/usr/bin/swift -e '
import Foundation

let center = DistributedNotificationCenter.default()
let userInfo: [String: Any] = [
    "enabled": true,
    "enable": true,
    "value": true,
    "isEnabled": true,
    "isGloableASRShortcutEnable": true
]

center.postNotificationName(
    Notification.Name("DoubaoImeSettings.enableGloableASRShortcutNotification"),
    object: nil,
    userInfo: userInfo,
    deliverImmediately: true
)

Thread.sleep(forTimeInterval: 0.2)
'

printf 'Requested DoubaoIme global ASR shortcut enable.\n'
