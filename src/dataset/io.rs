use crate::error::py_err;
use ignore::{WalkBuilder, overrides::OverrideBuilder};
use memmap2::{Mmap, MmapOptions};
use pyo3::prelude::*;
use std::{
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};

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
    let mut builder = WalkBuilder::new(root);

    if let Some(patterns) = patterns
        && !patterns.is_empty()
    {
        let overrides = build_overrides(root, patterns)?;
        builder.overrides(overrides);
    }

    let mut files = Vec::new();

    for result in builder.build() {
        let entry =
            result.map_err(|err| py_err(format!("failed to walk '{}': {err}", root.display())))?;

        if entry.depth() == 0 {
            continue;
        }

        let path = entry.path();

        if entry.file_type().is_some_and(|ft| ft.is_file()) && has_font_extension(path) {
            files.push(path.to_string_lossy().into_owned());
        }
    }

    files.sort_unstable();
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

fn build_overrides(root: &Path, patterns: &[String]) -> PyResult<ignore::overrides::Override> {
    let mut builder = OverrideBuilder::new(root);
    for pattern in patterns {
        builder
            .add(pattern)
            .map_err(|err| py_err(format!("invalid pattern '{pattern}': {err}")))?;
    }

    builder
        .build()
        .map_err(|err| py_err(format!("failed to compile patterns: {err}")))
}
