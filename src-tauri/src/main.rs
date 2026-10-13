// AURXON Investment Intelligence Hub - Native Tauri 2 Desktop Shell
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running AURXON desktop application");
}
