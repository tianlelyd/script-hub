import Foundation
import Carbon
import CoreGraphics

struct Hotkey {
    let keyCode: CGKeyCode
    let flags: CGEventFlags
    let holdDuration: useconds_t
}

enum ScriptError: Error {
    case invalidArgument(String)
    case missingArgument(String)
    case inputSourceNotFound(String)
}

func printUsage() {
    let usage = """
    用法: ifly_voice_trigger --start-key <key> --modifiers <mods> [其它选项]

    常用选项:
      --start-key <key> / --start-keycode <code>    启动语音的主键。
      --modifiers <command,option,...>              启动热键的修饰键列表。
      --start-hold <seconds>                        主键按住时长，默认 0.08。
      --target-id <id>                              目标输入法 ID，默认 com.iflytek.inputmethod.iFlytekIME.pinyin。
      --switch-delay <seconds>                      切换输入法后的等待时间，默认 0.3。
      --restore-delay <seconds>                     多久后切回原输入法，默认 2.0，设 0 表示不切回。
      --stop-key / --stop-keycode                   结束语音的主键。
      --stop-modifiers                              结束热键的修饰键，默认与启动相同。
      --stop-hold <seconds>                         结束主键按住时长，默认 0.08。
      --debug                                       输出更多日志。
    """
    print(usage)
}

enum Modifier: String {
    case command
    case option
    case control
    case shift
    case fn

    var flag: CGEventFlags {
        switch self {
        case .command: return .maskCommand
        case .option: return .maskAlternate
        case .control: return .maskControl
        case .shift: return .maskShift
        case .fn: return .maskSecondaryFn
        }
    }
}

let keyCodeMap: [String: CGKeyCode] = [
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
    "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "1": 18, "2": 19,
    "3": 20, "4": 21, "6": 22, "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28,
    "0": 29, "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37, ";": 41,
    "'": 39, "k": 40, "j": 38, ",": 43, ".": 47, "/": 44, "n": 45, "m": 46,
    "`": 50
]

func keyCode(for key: String) -> CGKeyCode? {
    let lower = key.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    switch lower {
    case "space": return 49
    case "return", "enter": return 36
    case "tab": return 48
    case "escape", "esc": return 53
    case "delete", "backspace": return 51
    case "up": return 126
    case "down": return 125
    case "left": return 123
    case "right": return 124
    default: break
    }

    if lower.hasPrefix("0x"), let code = UInt16(lower.dropFirst(2), radix: 16) {
        return CGKeyCode(code)
    }
    if let value = UInt16(lower) {
        return CGKeyCode(value)
    }
    if let code = keyCodeMap[lower] {
        return code
    }
    return nil
}

func parseModifiers(_ raw: String) throws -> CGEventFlags {
    let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    if trimmed == "none" || trimmed.isEmpty {
        return []
    }
    let parts = trimmed.split(separator: ",").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
    var flags = CGEventFlags()
    for part in parts where !part.isEmpty {
        guard let modifier = Modifier(rawValue: part) else {
            throw ScriptError.invalidArgument("未知修饰键: \(part)")
        }
        flags.insert(modifier.flag)
    }
    return flags
}

struct Options {
    var targetID = "com.iflytek.inputmethod.iFlytekIME.pinyin"
    var startKeyCode: CGKeyCode?
    var startHold: useconds_t = 80_000
    var startModifiers = CGEventFlags()
    var startModifiersProvided = false
    var stopKeyCode: CGKeyCode?
    var stopHold: useconds_t = 80_000
    var stopModifiers: CGEventFlags?
    var switchDelay: TimeInterval = 0.3
    var restoreDelay: TimeInterval = 2.0
    var debug = false
}

func parseOptions() throws -> (Options, Hotkey, Hotkey?) {
    var opts = Options()
    let args = CommandLine.arguments.dropFirst()

    if args.contains("--help") || args.contains("-h") {
        printUsage()
        exit(0)
    }

    func nextValue(_ label: String, iterator: inout ArraySlice<String>) throws -> String {
        guard let value = iterator.popFirst() else {
            throw ScriptError.missingArgument("\(label) 需要一个值")
        }
        return value
    }

    var iterator = args
    while let option = iterator.popFirst() {
        switch option {
        case "--target-id":
            opts.targetID = try nextValue(option, iterator: &iterator)
        case "--start-key":
            let raw = try nextValue(option, iterator: &iterator)
            guard let code = keyCode(for: raw) else {
                throw ScriptError.invalidArgument("无法识别的 start-key: \(raw)")
            }
            opts.startKeyCode = code
        case "--start-keycode":
            let raw = try nextValue(option, iterator: &iterator)
            guard let code = UInt16(raw) else {
                throw ScriptError.invalidArgument("start-keycode 需要整数")
            }
            opts.startKeyCode = CGKeyCode(code)
        case "--modifiers":
            let raw = try nextValue(option, iterator: &iterator)
            opts.startModifiers = try parseModifiers(raw)
            opts.startModifiersProvided = true
        case "--start-hold":
            let raw = try nextValue(option, iterator: &iterator)
            guard let value = Double(raw) else {
                throw ScriptError.invalidArgument("start-hold 需要数字")
            }
            opts.startHold = useconds_t(value * 1_000_000)
        case "--switch-delay":
            let raw = try nextValue(option, iterator: &iterator)
            guard let value = Double(raw) else {
                throw ScriptError.invalidArgument("switch-delay 需要数字")
            }
            opts.switchDelay = value
        case "--restore-delay":
            let raw = try nextValue(option, iterator: &iterator)
            guard let value = Double(raw) else {
                throw ScriptError.invalidArgument("restore-delay 需要数字")
            }
            opts.restoreDelay = value
        case "--stop-key":
            let raw = try nextValue(option, iterator: &iterator)
            guard let code = keyCode(for: raw) else {
                throw ScriptError.invalidArgument("无法识别的 stop-key: \(raw)")
            }
            opts.stopKeyCode = code
        case "--stop-keycode":
            let raw = try nextValue(option, iterator: &iterator)
            guard let code = UInt16(raw) else {
                throw ScriptError.invalidArgument("stop-keycode 需要整数")
            }
            opts.stopKeyCode = CGKeyCode(code)
        case "--stop-modifiers":
            let raw = try nextValue(option, iterator: &iterator)
            opts.stopModifiers = try parseModifiers(raw)
        case "--stop-hold":
            let raw = try nextValue(option, iterator: &iterator)
            guard let value = Double(raw) else {
                throw ScriptError.invalidArgument("stop-hold 需要数字")
            }
            opts.stopHold = useconds_t(value * 1_000_000)
        case "--debug":
            opts.debug = true
        default:
            throw ScriptError.invalidArgument("未知参数: \(option)")
        }
    }

    guard let startCode = opts.startKeyCode else {
        throw ScriptError.missingArgument("必须指定 --start-key 或 --start-keycode")
    }
    if !opts.startModifiersProvided {
        throw ScriptError.missingArgument("必须通过 --modifiers 指定修饰键（若无需修饰键可写 none）")
    }

    let startHotkey = Hotkey(keyCode: startCode, flags: opts.startModifiers, holdDuration: opts.startHold)
    var stopHotkey: Hotkey? = nil
    if let stopCode = opts.stopKeyCode {
        let stopFlags = opts.stopModifiers ?? opts.startModifiers
        stopHotkey = Hotkey(keyCode: stopCode, flags: stopFlags, holdDuration: opts.stopHold)
    } else if let _ = opts.stopModifiers {
        throw ScriptError.invalidArgument("已提供 --stop-modifiers 但缺少 stop-key/stop-keycode")
    }

    return (opts, startHotkey, stopHotkey)
}

func currentInputSourceID() -> String? {
    guard let source = TISCopyCurrentKeyboardInputSource()?.takeRetainedValue() else {
        return nil
    }
    guard let ptr = TISGetInputSourceProperty(source, kTISPropertyInputSourceID) else {
        return nil
    }
    let cfStr = Unmanaged<CFString>.fromOpaque(ptr).takeUnretainedValue()
    return cfStr as String
}

func selectInputSource(id: String) throws {
    let filter = [kTISPropertyInputSourceID as String: id] as CFDictionary
    guard let unmanagedList = TISCreateInputSourceList(filter, true) else {
        throw ScriptError.inputSourceNotFound(id)
    }
    let list = unmanagedList.takeRetainedValue() as NSArray
    guard let first = list.firstObject else {
        throw ScriptError.inputSourceNotFound(id)
    }
    let target = unsafeBitCast(first, to: TISInputSource.self)
    let status = TISSelectInputSource(target)
    if status != noErr {
        throw ScriptError.invalidArgument("切换输入源失败 (OSStatus=\(status))")
    }
}

func sendHotkey(_ hotkey: Hotkey) throws {
    guard let source = CGEventSource(stateID: .combinedSessionState) else {
        throw ScriptError.invalidArgument("无法创建 CGEventSource，检查辅助功能权限")
    }
    let down = CGEvent(keyboardEventSource: source, virtualKey: hotkey.keyCode, keyDown: true)
    down?.flags = hotkey.flags
    down?.post(tap: .cghidEventTap)
    usleep(hotkey.holdDuration)
    let up = CGEvent(keyboardEventSource: source, virtualKey: hotkey.keyCode, keyDown: false)
    up?.flags = hotkey.flags
    up?.post(tap: .cghidEventTap)
}

do {
    let (options, startHotkey, stopHotkey) = try parseOptions()

    guard let originalID = currentInputSourceID() else {
        throw ScriptError.invalidArgument("无法获取当前输入法，请确认终端被加入“辅助功能”白名单。")
    }

    if options.debug {
        fputs("当前输入源: \(originalID)\n", stderr)
        fputs("目标输入源: \(options.targetID)\n", stderr)
    }

    var switched = false
    if originalID != options.targetID {
        if options.debug { fputs("切换至讯飞输入法...\n", stderr) }
        try selectInputSource(id: options.targetID)
        switched = true
        Thread.sleep(forTimeInterval: options.switchDelay)
    }

    if options.debug { fputs("发送启动语音热键...\n", stderr) }
    try sendHotkey(startHotkey)

    if options.restoreDelay > 0 {
        if options.debug { fputs("等待 \(options.restoreDelay) 秒...\n", stderr) }
        Thread.sleep(forTimeInterval: options.restoreDelay)
        if let stop = stopHotkey {
            if options.debug { fputs("发送结束语音热键...\n", stderr) }
            try sendHotkey(stop)
        }
        if switched {
            if options.debug { fputs("切回原输入法...\n", stderr) }
            try selectInputSource(id: originalID)
        }
    } else if options.debug {
        fputs("restore-delay = 0，保持在讯飞输入法。\n", stderr)
    }

    if options.debug { fputs("完成。\n", stderr) }
} catch ScriptError.invalidArgument(let message) {
    fputs("参数错误: \(message)\n", stderr)
    printUsage()
    exit(1)
} catch ScriptError.missingArgument(let message) {
    fputs("缺少参数: \(message)\n", stderr)
    printUsage()
    exit(1)
} catch ScriptError.inputSourceNotFound(let id) {
    fputs("未找到输入源: \(id)。请在系统设置 > 键盘 > 输入法中启用。\n", stderr)
    exit(2)
} catch {
    fputs("执行失败: \(error)\n", stderr)
    exit(99)
}
