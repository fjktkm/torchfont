use crate::error::py_err;
use memmap2::{Mmap, MmapOptions};
use pyo3::prelude::*;
use std::{
    fs,
    path::{Path, PathBuf},
    sync::Arc,
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
    let mut files = WalkDir::new(root)
        .into_iter()
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            (entry.file_type().is_file() && has_font_extension(path))
                .then(|| path.to_string_lossy().into_owned())
        })
        .collect::<Vec<_>>();

    files.sort_unstable();

    if files.is_empty() {
        return Err(py_err(format!(
            "no font files found under '{}'",
            root.display()
        )));
    }

    Ok(files)
}

fn has_font_extension(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_ascii_lowercase())
        .map(|ext| matches!(ext.as_str(), "ttf" | "otf" | "ttc" | "otc"))
        .unwrap_or(false)
}

pub(super) fn map_font(path: &str) -> PyResult<Arc<Mmap>> {
    let file =
        fs::File::open(path).map_err(|err| py_err(format!("failed to open '{path}': {err}")))?;
    let mmap = unsafe { MmapOptions::new().map(&file) }
        .map_err(|err| py_err(format!("failed to map '{path}': {err}")))?;
    Ok(Arc::new(mmap))
}
