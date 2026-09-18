use tauri::{AppHandle, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};

/// Register Ctrl+Shift+Space (Windows/Linux) and Cmd+Shift+Space (macOS)
/// as a global toggle hotkey for the HUD overlay.
pub fn register_toggle_hotkey(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    // Primary: Ctrl+Shift+Space on Windows/Linux
    #[cfg(not(target_os = "macos"))]
    let shortcut_str = "Ctrl+Shift+Space";

    // macOS: Cmd+Shift+Space
    #[cfg(target_os = "macos")]
    let shortcut_str = "Cmd+Shift+Space";

    let shortcut: Shortcut = shortcut_str.parse()?;
    let app_handle = app.clone();

    app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, event| {
        if event.state == ShortcutState::Pressed {
            if let Some(window) = app_handle.get_webview_window("main") {
                if window.is_visible().unwrap_or(false) {
                    let _ = window.hide();
                } else {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        }
    })?;

    println!("[Codely] Global hotkey registered: {shortcut_str}");
    Ok(())
}
