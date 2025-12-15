mod entry;
mod index;
mod io;

use crate::error::py_index_err;
use entry::FontEntry;
use index::{DatasetIndex, load_entries_and_index};
use io::{canonicalize_root, discover_font_files};
use pyo3::prelude::*;

#[pyclass]
pub struct FontDataset {
    entries: Vec<FontEntry>,
    index: DatasetIndex,
}

#[pymethods]
impl FontDataset {
    #[new]
    pub fn new(
        root: String,
        codepoint_filter: Option<Vec<u32>>,
        patterns: Option<Vec<String>>,
    ) -> PyResult<Self> {
        let filter = codepoint_filter.map(|mut values| {
            values.sort_unstable();
            values.dedup();
            values
        });

        let root_path = canonicalize_root(&root)?;
        let files = discover_font_files(&root_path, patterns.as_deref())?;
        let (entries, index) = load_entries_and_index(files, filter.as_deref())?;

        Ok(Self { entries, index })
    }

    #[getter]
    pub fn sample_count(&self) -> usize {
        self.index.sample_offsets.last().copied().unwrap_or(0)
    }

    #[getter]
    pub fn style_class_count(&self) -> usize {
        self.index.inst_offsets.last().copied().unwrap_or(0)
    }

    #[getter]
    pub fn content_class_count(&self) -> usize {
        self.index.content_classes.len()
    }

    pub fn locate(&self, idx: usize) -> PyResult<(usize, Option<usize>, u32, usize, usize)> {
        let total = self.sample_count();
        if idx >= total {
            return Err(py_index_err(format!(
                "sample index {idx} out of range (len={total})"
            )));
        }

        let font_idx = self
            .index
            .sample_offsets
            .partition_point(|offset| *offset <= idx)
            - 1;

        let entry = &self.entries[font_idx];
        let font_start = self.index.sample_offsets[font_idx];
        let sample_idx = idx - font_start;
        let cp_count = entry.codepoints.len();
        debug_assert!(
            cp_count > 0,
            "font '{}' has no indexed code points",
            &entry.path
        );

        let inst_start = self.index.inst_offsets[font_idx];
        let inst_idx = sample_idx / cp_count;
        debug_assert!(
            inst_idx < entry.instance_count(),
            "instance index {} out of range for font '{}'",
            inst_idx,
            &entry.path
        );

        let cp_offset = sample_idx % cp_count;
        let cp = entry.codepoints[cp_offset];
        let style_idx = inst_start + inst_idx;
        let content_idx = self.index.content_index(cp)?;
        let instance = entry.is_variable().then_some(inst_idx);

        Ok((font_idx, instance, cp, style_idx, content_idx))
    }

    pub fn item(&self, idx: usize) -> PyResult<(Vec<i32>, Vec<f32>, usize, usize)> {
        let (font_idx, inst_idx, codepoint, style_idx, content_idx) = self.locate(idx)?;
        self.entries[font_idx]
            .glyph(codepoint, inst_idx)
            .map(|(types, coords)| (types, coords, style_idx, content_idx))
    }
}
