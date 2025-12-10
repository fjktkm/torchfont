use skrifa::outline::OutlinePen;

#[derive(Clone, Copy)]
#[repr(i32)]
enum Command {
    MoveTo = 1,
    LineTo = 2,
    CurveTo = 3,
    ClosePath = 4,
    End = 5,
}

pub struct SegmentPen {
    commands: Vec<i32>,
    coords: Vec<f32>,
    scale: f32,
    current: Option<(f32, f32)>,
    start: Option<(f32, f32)>,
}

impl SegmentPen {
    pub fn new(units_per_em: f32) -> Self {
        debug_assert!(units_per_em > 0.0, "units_per_em must be positive");
        let scale = units_per_em.recip();
        Self {
            commands: Vec::new(),
            coords: Vec::new(),
            scale,
            current: None,
            start: None,
        }
    }

    pub fn finish(mut self) -> (Vec<i32>, Vec<f32>) {
        self.push(Command::End, [0.0; 6]);
        (self.commands, self.coords)
    }

    fn push(&mut self, command: Command, values: [f32; 6]) {
        self.commands.push(command as i32);
        let scaled = values.map(|value| value * self.scale);
        self.coords.extend_from_slice(&scaled);
    }
}

impl OutlinePen for SegmentPen {
    fn move_to(&mut self, x: f32, y: f32) {
        self.push(Command::MoveTo, [0.0, 0.0, 0.0, 0.0, x, y]);
        self.current = Some((x, y));
        self.start = Some((x, y));
    }

    fn line_to(&mut self, x: f32, y: f32) {
        self.push(Command::LineTo, [0.0, 0.0, 0.0, 0.0, x, y]);
        self.current = Some((x, y));
    }

    fn quad_to(&mut self, cx0: f32, cy0: f32, x: f32, y: f32) {
        let (px, py) = self.current.expect("quad_to requires an active point");
        let cp1x = px + (2.0 / 3.0) * (cx0 - px);
        let cp1y = py + (2.0 / 3.0) * (cy0 - py);
        let cp2x = x + (2.0 / 3.0) * (cx0 - x);
        let cp2y = y + (2.0 / 3.0) * (cy0 - y);
        self.push(Command::CurveTo, [cp1x, cp1y, cp2x, cp2y, x, y]);
        self.current = Some((x, y));
    }

    fn curve_to(&mut self, cx0: f32, cy0: f32, cx1: f32, cy1: f32, x: f32, y: f32) {
        let _ = self.current.expect("curve_to requires an active point");
        self.push(Command::CurveTo, [cx0, cy0, cx1, cy1, x, y]);
        self.current = Some((x, y));
    }

    fn close(&mut self) {
        let start = self.start.expect("close requires an active contour");
        self.push(Command::ClosePath, [0.0; 6]);
        self.current = Some(start);
    }
}
