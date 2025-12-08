mod entry;
mod fs;

use entry::FontEntry;
use fs::{canonicalize_root, discover_font_files};
use pyo3::prelude::*;

#[pyclass]
pub struct FontDataset {
    entries: Vec<FontEntry>,
    index: DatasetIndex,
}

#[pymethods]
impl FontDataset {
    #[new]
    pub fn new(root: String, codepoint_filter: Option<Vec<u32>>) -> PyResult<Self> {
        let filter = codepoint_filter.map(|mut values| {
            values.sort_unstable();
            values.dedup();
            values
        });
        let filter_ref = filter.as_deref();

        let root_path = canonicalize_root(&root)?;
        let files = discover_font_files(&root_path)?;

        let entries = files
            .iter()
            .map(|path| FontEntry::load(path, filter_ref))
            .collect::<PyResult<Vec<_>>>()?;

        let index = DatasetIndex::build(&entries);

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
            return Err(py_err(format!(
                "sample index {idx} out of range (len={total})"
            )));
        }

        if self.entries.is_empty() {
            return Err(py_err("font collection is empty".to_string()));
        }

        let pos = self
            .index
            .sample_offsets
            .partition_point(|offset| *offset <= idx);
        let font_idx = pos.saturating_sub(1).min(self.entries.len() - 1);

        let font_start = self.index.sample_offsets[font_idx];
        let sample_idx = idx - font_start;
        let cp_start = self.index.cp_offsets[font_idx];
        let cp_end = self.index.cp_offsets[font_idx + 1];
        let cp_count = cp_end - cp_start;

        if cp_count == 0 {
            return Err(py_err(format!(
                "font '{}' has no indexed code points",
                self.entries[font_idx].path
            )));
        }

        let inst_count = self.index.inst_counts[font_idx];
        let inst_idx = sample_idx / cp_count;
        if inst_idx >= inst_count {
            return Err(py_err(format!(
                "instance index {inst_idx} out of range for font '{}'",
                self.entries[font_idx].path
            )));
        }

        let cp_offset = sample_idx % cp_count;
        let cp = self.index.flat_cps[cp_start + cp_offset];
        let style_idx = self.index.inst_offsets[font_idx] + inst_idx;
        let content_idx = self
            .index
            .content_classes
            .binary_search(&cp)
            .map_err(|_| py_err(format!("codepoint U+{cp:04X} missing from index")))?;
        let instance = if self.index.is_variable[font_idx] {
            Some(inst_idx)
        } else {
            None
        };

        Ok((font_idx, instance, cp, style_idx, content_idx))
    }

    pub fn item(&self, idx: usize) -> PyResult<(Vec<i32>, Vec<f32>, usize, usize)> {
        let (font_idx, inst_idx, codepoint, style_idx, content_idx) = self.locate(idx)?;
        let entry = self
            .entries
            .get(font_idx)
            .ok_or_else(|| py_err(format!("font index {font_idx} out of range")))?;

        let (types, coords) = entry.glyph(codepoint, inst_idx)?;

        Ok((types, coords, style_idx, content_idx))
    }
}

pub(crate) fn py_err(msg: String) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyValueError, _>(msg)
}

struct DatasetIndex {
    sample_offsets: Vec<usize>,
    inst_offsets: Vec<usize>,
    cp_offsets: Vec<usize>,
    flat_cps: Vec<u32>,
    content_classes: Vec<u32>,
    inst_counts: Vec<usize>,
    is_variable: Vec<bool>,
}

impl DatasetIndex {
    fn build(entries: &[FontEntry]) -> Self {
        let mut sample_offsets = Vec::with_capacity(entries.len() + 1);
        let mut inst_offsets = Vec::with_capacity(entries.len() + 1);
        let mut cp_offsets = Vec::with_capacity(entries.len() + 1);
        let mut flat_cps = Vec::new();
        let mut inst_counts = Vec::with_capacity(entries.len());
        let mut is_variable = Vec::with_capacity(entries.len());

        sample_offsets.push(0);
        inst_offsets.push(0);
        cp_offsets.push(0);

        for entry in entries {
            let cp_count = entry.codepoints.len();
            flat_cps.extend_from_slice(&entry.codepoints);
            cp_offsets.push(flat_cps.len());

            let inst_count = entry.instance_count();
            inst_counts.push(inst_count);
            is_variable.push(entry.is_variable());

            let next_samples = sample_offsets.last().unwrap() + cp_count * inst_count;
            sample_offsets.push(next_samples);

            let next_inst = inst_offsets.last().unwrap() + inst_count;
            inst_offsets.push(next_inst);
        }

        let mut content_classes = flat_cps.clone();
        content_classes.sort_unstable();
        content_classes.dedup();

        Self {
            sample_offsets,
            inst_offsets,
            cp_offsets,
            flat_cps,
            content_classes,
            inst_counts,
            is_variable,
        }
    }
}
