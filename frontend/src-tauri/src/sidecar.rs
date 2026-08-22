use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::AppHandle;

static SIDECAR_CHILD: Mutex<Option<Child>> = Mutex::new(None);

/// Attempt to start the compiled backend binary if present in the app resources.
/// In dev mode, the user runs the Python server separately.
pub fn start_backend_sidecar(_app: &AppHandle) {
    let mut child_guard = SIDECAR_CHILD.lock().unwrap();

    // Check if bundled cluely-backend.exe exists in current directory or sidecars dir
    let candidates = [
        "cluely-backend.exe",
        "backend.exe",
        "../backend/dist/cluely-backend.exe",
    ];

    for candidate in &candidates {
        if std::path::Path::new(candidate).exists() {
            println!("[Cluely] Launching backend sidecar: {candidate}");
            if let Ok(child) = Command::new(candidate).spawn() {
                *child_guard = Some(child);
                println!("[Cluely] Backend sidecar started successfully.");
                return;
            }
        }
    }

    println!("[Cluely] No local sidecar binary found — running against external dev server on http://127.0.0.1:8000");
}

/// Gracefully kill the sidecar when the application quits.
#[allow(dead_code)]
pub fn kill_backend_sidecar() {
    let mut child_guard = SIDECAR_CHILD.lock().unwrap();
    if let Some(mut child) = child_guard.take() {
        println!("[Cluely] Shutting down backend sidecar process...");
        let _ = child.kill();
    }
}
