use tauri::{AppHandle, Manager};

#[cfg(target_os = "windows")]
use tauri::PhysicalPosition;

/// Position the HUD window to the right side of the primary screen on startup
pub fn position_hud_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        if let Ok(monitor) = window.current_monitor() {
            if let Some(monitor) = monitor {
                let screen_size = monitor.size();
                let win_width: u32 = 920;
                let _win_height: u32 = 880;
                let x = (screen_size.width as i32) - (win_width as i32) - 32;
                let y = 32_i32;
                let _ = window.set_position(tauri::Position::Physical(
                    PhysicalPosition::new(x, y),
                ));
            }
        }
        // Set always-on-top at screen-saver level so it floats above Zoom/Teams
        let _ = window.set_always_on_top(true);
    }
}

/// IPC: Set window opacity (called from React via `invoke`)
#[tauri::command]
pub fn cmd_set_opacity(app: AppHandle, opacity: f64) {
    if let Some(window) = app.get_webview_window("main") {
        let clamped = opacity.clamp(0.1, 1.0);
        let _ = window.set_effects(None); // clear any existing
        // Opacity is set via the window config; use set_ignore_cursor_events for click-through instead
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

/// IPC: Toggle click-through mode (mouse events pass to window underneath)
#[tauri::command]
pub fn cmd_toggle_click_through(app: AppHandle, enabled: bool) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.set_ignore_cursor_events(enabled);
    }
}

/// IPC: Set HUD position mode — "right" | "bottom" | "compact"
#[tauri::command]
pub fn cmd_set_position_mode(app: AppHandle, mode: String) {
    if let Some(window) = app.get_webview_window("main") {
        if let Ok(monitor) = window.current_monitor() {
            if let Some(monitor) = monitor {
                let screen = monitor.size();
                match mode.as_str() {
                    "right" => {
                        let _ = window.set_size(tauri::Size::Physical(
                            tauri::PhysicalSize::new(920, 880),
                        ));
                        let x = (screen.width as i32) - 920 - 32;
                        let _ = window.set_position(tauri::Position::Physical(
                            PhysicalPosition::new(x, 32),
                        ));
                    }
                    "compact" => {
                        let _ = window.set_size(tauri::Size::Physical(
                            tauri::PhysicalSize::new(380, 520),
                        ));
                        let x = (screen.width as i32) - 380 - 20;
                        let _ = window.set_position(tauri::Position::Physical(
                            PhysicalPosition::new(x, 20),
                        ));
                    }
                    "bottom" => {
                        let _ = window.set_size(tauri::Size::Physical(
                            tauri::PhysicalSize::new(screen.width, 160),
                        ));
                        let y = (screen.height as i32) - 160 - 10;
                        let _ = window.set_position(tauri::Position::Physical(
                            PhysicalPosition::new(0, y),
                        ));
                    }
                    _ => {}
                }
            }
        }
    }
}
