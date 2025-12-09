use super::{io::map_font, py_err};
use crate::pen::TensorPen;
use memmap2::Mmap;
use pyo3::prelude::*;
use skrifa::raw::TableProvider;
use skrifa::{
    GlyphId, MetadataProvider,
    charmap::Charmap,
    instance::{Location, LocationRef, Size},
    outline::DrawSettings,
};
use std::sync::Arc;

pub(super) struct FontEntry {
    pub(super) path: String,
    data: Arc<Mmap>,
    pub(super) codepoints: Vec<u32>,
    glyph_ids: Vec<GlyphId>,
    units_per_em: f32,
    locations: Vec<Location>,
}

impl FontEntry {
    pub(super) fn load(path: &str, filter: Option<&[u32]>) -> PyResult<Self> {
        let mapped = map_font(path)?;
        let font = font_ref(&mapped, path)?;

        let upem = font
            .head()
            .map_err(|_| py_err(format!("font '{path}' is missing a head table")))?
            .units_per_em();

        let mut mappings: Vec<_> = Charmap::new(&font)
            .mappings()
            .filter(|(codepoint, _)| accept_codepoint(filter, *codepoint))
            .collect();
        mappings.sort_unstable_by_key(|entry| entry.0);
        let (codepoints, glyph_ids): (Vec<_>, Vec<_>) = mappings.into_iter().unzip();

        let axes_count = font.axes().len();
        let locations = font
            .named_instances()
            .iter()
            .map(|instance| {
                let mut location = Location::new(axes_count);
                instance.location_to_slice(location.coords_mut());
                location
            })
            .collect();

        Ok(Self {
            path: path.to_string(),
            data: mapped,
            codepoints,
            glyph_ids,
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
        let font = font_ref(&self.data, &self.path)?;
        let glyph = font.outline_glyphs().get(glyph_id).ok_or_else(|| {
            py_err(format!(
                "glyph id {} missing from '{}'",
                glyph_id.to_u32(),
                self.path
            ))
        })?;

        let mut pen = TensorPen::new(self.units_per_em);
        glyph
            .draw(
                DrawSettings::unhinted(Size::unscaled(), self.location_ref(instance_index)?),
                &mut pen,
            )
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
        self.codepoints
            .binary_search(&codepoint)
            .map(|idx| self.glyph_ids[idx])
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
    filter.map_or(true, |values| values.binary_search(&codepoint).is_ok())
}

fn font_ref<'a>(data: &'a Mmap, path: &str) -> PyResult<skrifa::FontRef<'a>> {
    skrifa::FontRef::from_index(&data[..], 0)
        .map_err(|err| py_err(format!("failed to parse '{path}': {err}")))
}
