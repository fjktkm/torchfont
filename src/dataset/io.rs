use crate::error::py_err;
use ignore::overrides::{Override, OverrideBuilder};
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

pub(super) fn discover_font_files(
    root: &Path,
    patterns: Option<&[String]>,
) -> PyResult<Vec<String>> {
    let overrides = build_overrides(root, patterns)?;
    let mut files = Vec::new();
    let mut walker = WalkDir::new(root).into_iter();

    while let Some(entry) = walker.next() {
        let entry =
            entry.map_err(|err| py_err(format!("failed to walk '{}': {err}", root.display())))?;

        if entry.depth() == 0 {
            continue;
        }

        let path = entry.path();
        let is_dir = entry.file_type().is_dir();

        if let Some(ref overrides) = overrides {
            let rel = match path.strip_prefix(root) {
                Ok(rel) => rel,
                Err(_) => continue,
            };
            let rel_str = rel.to_string_lossy();
            let matched = overrides.matched(rel_str.as_ref(), is_dir);

            if matched.is_ignore() {
                if is_dir {
                    walker.skip_current_dir();
                }
                continue;
            }

            if !is_dir && !matched.is_whitelist() {
                continue;
            }
        }

        if !is_dir && has_font_extension(path) {
            files.push(path.to_string_lossy().into_owned());
        }
    }

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

fn build_overrides(root: &Path, patterns: Option<&[String]>) -> PyResult<Option<Override>> {
    let patterns = match patterns {
        Some(values) if !values.is_empty() => values,
        _ => return Ok(None),
    };

    let mut builder = OverrideBuilder::new(root);
    for pattern in patterns {
        builder
            .add(pattern)
            .map_err(|err| py_err(format!("invalid pattern '{pattern}': {err}")))?;
    }

    builder
        .build()
        .map(Some)
        .map_err(|err| py_err(format!("failed to compile patterns: {err}")))
}
