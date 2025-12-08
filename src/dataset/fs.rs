use super::py_err;
use pyo3::prelude::*;
use std::{
    fs,
    path::{Path, PathBuf},
};
use walkdir::WalkDir;

pub(super) fn canonicalize_root(root: &str) -> PyResult<PathBuf> {
    let expanded = shellexpand::tilde(root);
    let path = PathBuf::from(expanded.as_ref());
    fs::canonicalize(&path).map_err(|err| {
        py_err(format!(
            "failed to resolve font root '{}': {err}",
            path.display()
        ))
    })
}

pub(super) fn discover_font_files(root: &Path) -> PyResult<Vec<String>> {
    if !root.exists() {
        return Err(py_err(format!(
            "font root '{}' does not exist",
            root.display()
        )));
    }

    let mut files = Vec::new();
    for entry in WalkDir::new(root)
        .into_iter()
        .filter_map(Result::ok)
        .filter(|e| e.file_type().is_file())
    {
        let path = entry.path();
        if has_font_extension(path) {
            files.push(path.to_string_lossy().into_owned());
        }
    }

    files.sort();

    if files.is_empty() {
        Err(py_err(format!(
            "no font files found under '{}'",
            root.display()
        )))
    } else {
        Ok(files)
    }
}

fn has_font_extension(path: &Path) -> bool {
    match path.extension().and_then(|ext| ext.to_str()) {
        Some(ext) if ext.eq_ignore_ascii_case("ttf") => true,
        Some(ext) if ext.eq_ignore_ascii_case("otf") => true,
        _ => false,
    }
}
