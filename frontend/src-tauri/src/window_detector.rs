use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tauri::AppHandle;

#[allow(unused_imports)]
use tauri::Emitter;

#[cfg(windows)]
use windows_sys::Win32::UI::WindowsAndMessaging::{GetForegroundWindow, GetWindowTextW};

/// Start background polling of the active foreground window title.
/// When VS Code, Cursor, or an IDE is active, emits `repo-detected` event to the webview.
#[allow(unused_variables)]
pub fn start_window_detection(app: AppHandle) {
    let running = Arc::new(AtomicBool::new(true));

    std::thread::spawn(move || {
        #[allow(unused_mut)]
        let mut last_title = String::new();

        while running.load(Ordering::Relaxed) {
            std::thread::sleep(Duration::from_millis(2500));

            #[cfg(windows)]
            {
                let hwnd = unsafe { GetForegroundWindow() };
                if hwnd != std::ptr::null_mut() {
                    let mut buffer = [0u16; 512];
                    let len = unsafe { GetWindowTextW(hwnd, buffer.as_mut_ptr(), 512) };
                    if len > 0 {
                        let title = String::from_utf16_lossy(&buffer[..len as usize]);

                        if title != last_title {
                            last_title = title.clone();

                            // Look for common IDE title formats:
                            // VS Code: "file.py - project_name - Visual Studio Code"
                            // Cursor: "file.py - project_name - Cursor"
                            // PyCharm: "project_name – [file.py] – PyCharm"
                            let title_lower = title.to_lowercase();
                            let is_ide = title_lower.contains("visual studio code")
                                || title_lower.contains("cursor")
                                || title_lower.contains("pycharm")
                                || title_lower.contains("intellij")
                                || title_lower.contains("sublime text");

                            if is_ide {
                                // Extract project name from title segments
                                let parts: Vec<&str> = title.split(" - ").collect();
                                let project_hint = if parts.len() >= 2 {
                                    parts[parts.len() - 2].trim().to_string()
                                } else {
                                    parts[0].trim().to_string()
                                };

                                let _ = app.emit(
                                    "repo-detected",
                                    serde_json::json!({
                                        "window_title": title,
                                        "project_hint": project_hint,
                                    }),
                                );
                            }
                        }
                    }
                }
            }
        }
    });
}
