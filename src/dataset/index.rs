use super::{entry::FontEntry, py_err};
use pyo3::prelude::*;

pub(super) struct DatasetIndex {
    pub(super) sample_offsets: Vec<usize>,
    pub(super) inst_offsets: Vec<usize>,
    pub(super) content_classes: Vec<u32>,
}

impl DatasetIndex {
    pub(super) fn content_index(&self, codepoint: u32) -> PyResult<usize> {
        self.content_classes
            .binary_search(&codepoint)
            .map_err(|_| py_err(format!("codepoint U+{codepoint:04X} missing from index")))
    }
}

pub(super) fn load_entries_and_index(
    files: Vec<String>,
    filter: Option<&[u32]>,
) -> PyResult<(Vec<FontEntry>, DatasetIndex)> {
    let mut entries = Vec::with_capacity(files.len());
    let mut sample_offsets = Vec::with_capacity(files.len() + 1);
    let mut inst_offsets = Vec::with_capacity(files.len() + 1);
    let mut all_cps = Vec::new();

    let (mut sample_total, mut inst_total) = (0usize, 0usize);
    sample_offsets.push(sample_total);
    inst_offsets.push(inst_total);

    for path in files {
        let entry = FontEntry::load(&path, filter)?;
        let cp_count = entry.codepoints.len();
        let inst_count = entry.instance_count();

        sample_total += cp_count * inst_count;
        sample_offsets.push(sample_total);

        inst_total += inst_count;
        inst_offsets.push(inst_total);

        all_cps.extend_from_slice(&entry.codepoints);
        entries.push(entry);
    }

    let mut content_classes = all_cps;
    content_classes.sort_unstable();
    content_classes.dedup();

    let index = DatasetIndex {
        sample_offsets,
        inst_offsets,
        content_classes,
    };

    Ok((entries, index))
}
