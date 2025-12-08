use super::py_err;
use crate::pen::TensorPen;
use memmap2::{Mmap, MmapOptions};
use pyo3::prelude::*;
use skrifa::raw::TableProvider;
use skrifa::{
    GlyphId, MetadataProvider,
    charmap::Charmap,
    instance::{Location, LocationRef, Size},
    outline::DrawSettings,
};
use std::{fs::File, mem, path::Path, sync::Arc};

pub(super) struct FontEntry {
    pub(super) path: String,
    #[allow(dead_code)]
    data: Arc<Mmap>,
    font: skrifa::FontRef<'static>,
    glyph_map: Vec<(u32, GlyphId)>,
    pub(super) codepoints: Vec<u32>,
    units_per_em: f32,
    locations: Vec<Location>,
}

impl FontEntry {
    pub(super) fn load(path: &str, filter: Option<&[u32]>) -> PyResult<Self> {
        let mapped = map_font(path)?;
        let font = skrifa::FontRef::from_index(&mapped[..], 0)
            .map_err(|err| py_err(format!("failed to parse '{path}': {err}")))?;
        let static_font: skrifa::FontRef<'static> = unsafe { mem::transmute(font) };

        let head = static_font
            .head()
            .map_err(|_| py_err(format!("font '{path}' is missing a head table")))?;
        let upem = head.units_per_em();

        let charmap = Charmap::new(&static_font);
        let mut glyph_map: Vec<_> = charmap
            .mappings()
            .filter(|(codepoint, _)| accept_codepoint(filter, *codepoint))
            .collect();
        glyph_map.sort_unstable_by_key(|entry| entry.0);
        let codepoints = glyph_map.iter().map(|(cp, _)| *cp).collect();

        let axes = static_font.axes();
        let axes_count = axes.len();
        let named_instances = static_font.named_instances();
        let locations = (0..named_instances.len())
            .filter_map(|idx| named_instances.get(idx))
            .map(|instance| {
                let mut location = Location::new(axes_count);
                instance.location_to_slice(location.coords_mut());
                location
            })
            .collect();

        Ok(Self {
            path: path.to_string(),
            data: mapped,
            font: static_font,
            glyph_map,
            codepoints,
            units_per_em: upem as f32,
            locations,
        })
    }

    pub(super) fn glyph(
        &self,
        codepoint: u32,
        instance_index: Option<usize>,
    ) -> PyResult<(Vec<i32>, Vec<f32>)> {
        let glyph_id = self.lookup_glyph(codepoint)?;
        let outlines = self.font.outline_glyphs();
        let glyph = outlines.get(glyph_id).ok_or_else(|| {
            py_err(format!(
                "glyph id {} missing from '{}'",
                glyph_id.to_u32(),
                self.path
            ))
        })?;

        let location = self.location_ref(instance_index)?;
        let mut pen = TensorPen::new(self.units_per_em);
        glyph
            .draw(DrawSettings::unhinted(Size::unscaled(), location), &mut pen)
            .map_err(|err| py_err(format!("failed to draw glyph: {err}")))?;

        Ok(pen.finish())
    }

    pub(super) fn instance_count(&self) -> usize {
        self.locations.len().max(1)
    }

    pub(super) fn is_variable(&self) -> bool {
        !self.locations.is_empty()
    }

    fn lookup_glyph(&self, codepoint: u32) -> PyResult<GlyphId> {
        self.glyph_map
            .binary_search_by_key(&codepoint, |entry| entry.0)
            .map(|idx| self.glyph_map[idx].1)
            .map_err(|_| {
                py_err(format!(
                    "codepoint U+{codepoint:04X} missing from '{}'",
                    self.path
                ))
            })
    }

    fn location_ref(&self, index: Option<usize>) -> PyResult<LocationRef<'_>> {
        if let Some(idx) = index {
            let location = self.locations.get(idx).ok_or_else(|| {
                py_err(format!(
                    "instance index {idx} out of range for '{}'",
                    self.path
                ))
            })?;
            Ok(LocationRef::from(location))
        } else {
            Ok(LocationRef::default())
        }
    }
}

fn accept_codepoint(filter: Option<&[u32]>, codepoint: u32) -> bool {
    match filter {
        Some(values) => values.binary_search(&codepoint).is_ok(),
        None => true,
    }
}

fn map_font(path: &str) -> PyResult<Arc<Mmap>> {
    let file = File::open(Path::new(path))
        .map_err(|err| py_err(format!("failed to open '{path}': {err}")))?;
    let mmap = unsafe { MmapOptions::new().map(&file) }
        .map_err(|err| py_err(format!("failed to map '{path}': {err}")))?;
    Ok(Arc::new(mmap))
}
