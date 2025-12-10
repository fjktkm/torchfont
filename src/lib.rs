mod dataset;
mod error;
mod pen;

use dataset::FontDataset;
use pyo3::{Bound, prelude::*, types::PyModule};

#[pymodule]
fn _torchfont(_py: Python<'_>, m: Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FontDataset>()?;
    Ok(())
}
