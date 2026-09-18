// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod hotkey;
mod sidecar;
mod tray;
mod window;
mod window_detector;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .setup(|app| {
            let app_handle = app.handle().clone();

            // 1. Position window to the right side of the primary screen
            window::position_hud_window(&app_handle);

            // 2. Register global hotkey: Ctrl+Shift+Space / Cmd+Shift+Space
            hotkey::register_toggle_hotkey(&app_handle)?;

            // 3. Set up system tray icon + menu
            tray::setup_tray(&app_handle)?;

            // 4. Start active IDE foreground window detector
            window_detector::start_window_detection(app_handle.clone());

            // 5. Start backend sidecar if compiled binary exists
            sidecar::start_backend_sidecar(&app_handle);

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            window::cmd_set_opacity,
            window::cmd_minimize_window,
            window::cmd_close_window,
            window::cmd_toggle_click_through,
            window::cmd_set_position_mode,
            window::cmd_set_stealth_mode,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Codely");
}
