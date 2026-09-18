use tauri::{AppHandle, LogicalPosition, LogicalSize, Manager, WebviewWindow};

#[cfg(target_os = "windows")]
use windows_sys::Win32::UI::WindowsAndMessaging::SetWindowDisplayAffinity;

/// Applies OS-level screen capture invisibility (Stealth Mode).
/// Excludes the HUD from Zoom, Microsoft Teams, Google Meet, OBS, and screenshot capture.
pub fn apply_stealth_mode(window: &WebviewWindow, enabled: bool) {
    #[cfg(target_os = "windows")]
    {
        if let Ok(hwnd) = window.hwnd() {
            // WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Windows 10 2004+)
            // WDA_NONE = 0x00000000
            let affinity: u32 = if enabled { 0x00000011 } else { 0x00000000 };
            unsafe {
                SetWindowDisplayAffinity(hwnd.0 as _, affinity);
            }
        }
    }
}

/// Position the HUD window to the right side of the primary screen on startup
pub fn position_hud_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        if let Ok(Some(monitor)) = window.current_monitor() {
            let scale = monitor.scale_factor();
            let screen = monitor.size().to_logical::<f64>(scale);
            let win_width = 720.0;
            let win_height = (screen.height - 80.0).max(540.0);
            let x = screen.width - win_width - 24.0;
            let y = 24.0;
            let _ = window.set_size(tauri::Size::Logical(LogicalSize::new(win_width, win_height)));
            let _ = window.set_position(tauri::Position::Logical(LogicalPosition::new(x, y)));
        }
        // Set always-on-top so it floats above Zoom/Teams
        let _ = window.set_always_on_top(true);

        // Enable screen capture invisibility by default
        apply_stealth_mode(&window, true);
    }
}

/// IPC: Toggle screen-capture invisibility ("Stealth Mode")
#[tauri::command]
pub fn cmd_set_stealth_mode(app: AppHandle, enabled: bool) {
    if let Some(window) = app.get_webview_window("main") {
        apply_stealth_mode(&window, enabled);
    }
}

/// IPC: Set window opacity (called from React via `invoke`)
#[tauri::command]
pub fn cmd_set_opacity(app: AppHandle, opacity: f64) {
    if let Some(window) = app.get_webview_window("main") {
        let clamped = opacity.clamp(0.1, 1.0);
        let _ = window.set_effects(None);
        let _ = window.set_ignore_cursor_events(clamped < 0.3);
    }
}

/// IPC: Minimize window to taskbar
#[tauri::command]
pub fn cmd_minimize_window(app: AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.minimize();
    }
}

/// IPC: Close window (quits app)
#[tauri::command]
pub fn cmd_close_window(app: AppHandle) {
    app.exit(0);
}

/// IPC: Toggles ignore cursor events (click-through overlay)
#[tauri::command]
pub fn cmd_toggle_click_through(app: AppHandle, enabled: bool) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.set_ignore_cursor_events(enabled);
    }
}

/// IPC: Set HUD position mode — "right" (DOCK) | "compact" (MINI) | "bottom" (STRIP)
#[tauri::command]
pub fn cmd_set_position_mode(app: AppHandle, mode: String) {
    if let Some(window) = app.get_webview_window("main") {
        if let Ok(Some(monitor)) = window.current_monitor() {
            let scale = monitor.scale_factor();
            let screen = monitor.size().to_logical::<f64>(scale);
            match mode.as_str() {
                "right" | "dock" => {
                    let w = 720.0;
                    let h = (screen.height - 80.0).max(540.0);
                    let x = screen.width - w - 24.0;
                    let y = 24.0;
                    let _ = window.set_size(tauri::Size::Logical(LogicalSize::new(w, h)));
                    let _ = window.set_position(tauri::Position::Logical(LogicalPosition::new(x, y)));
                }
                "compact" | "mini" => {
                    let w = 440.0;
                    let h = (screen.height - 80.0).min(640.0);
                    let x = screen.width - w - 24.0;
                    let y = 24.0;
                    let _ = window.set_size(tauri::Size::Logical(LogicalSize::new(w, h)));
                    let _ = window.set_position(tauri::Position::Logical(LogicalPosition::new(x, y)));
                }
                "bottom" | "strip" => {
                    let w = (screen.width - 48.0).max(600.0);
                    let h = 160.0;
                    let x = 24.0;
                    let y = screen.height - h - 56.0;
                    let _ = window.set_size(tauri::Size::Logical(LogicalSize::new(w, h)));
                    let _ = window.set_position(tauri::Position::Logical(LogicalPosition::new(x, y)));
                }
                _ => {}
            }
        }
    }
}
