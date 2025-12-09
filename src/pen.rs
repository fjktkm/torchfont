use skrifa::outline::OutlinePen;

pub struct TensorPen {
    commands: Vec<i32>,
    coords: Vec<f32>,
    scale: f32,
    current: Option<(f32, f32)>,
    contour_start: Option<(f32, f32)>,
}

impl TensorPen {
    pub fn new(units_per_em: f32) -> Self {
        let scale = if units_per_em > 0.0 {
            1.0 / units_per_em
        } else {
            1.0
        };
        Self {
            commands: Vec::new(),
            coords: Vec::new(),
            scale,
            current: None,
            contour_start: None,
        }
    }

    pub fn finish(mut self) -> (Vec<i32>, Vec<f32>) {
        self.push(Command::End, [0.0; 6]);
        (self.commands, self.coords)
    }

    fn push(&mut self, command: Command, values: [f32; 6]) {
        self.commands.push(command as i32);
        if self.scale == 1.0 {
            self.coords.extend_from_slice(&values);
        } else {
            self.coords
                .extend(values.iter().map(|value| value * self.scale));
        }
    }

    fn push_endpoint(&mut self, command: Command, x: f32, y: f32) {
        self.push(command, [0.0, 0.0, 0.0, 0.0, x, y]);
        self.current = Some((x, y));
    }

    fn cubic(&mut self, coords: [f32; 6]) {
        self.push(Command::CurveTo, coords);
        self.current = Some((coords[4], coords[5]));
    }
}

impl OutlinePen for TensorPen {
    fn move_to(&mut self, x: f32, y: f32) {
        self.push_endpoint(Command::MoveTo, x, y);
        self.contour_start = Some((x, y));
    }

    fn line_to(&mut self, x: f32, y: f32) {
        self.push_endpoint(Command::LineTo, x, y);
    }

    fn quad_to(&mut self, cx0: f32, cy0: f32, x: f32, y: f32) {
        let (px, py) = self.current.unwrap_or((cx0, cy0));
        let cp1x = px + (2.0 / 3.0) * (cx0 - px);
        let cp1y = py + (2.0 / 3.0) * (cy0 - py);
        let cp2x = x + (2.0 / 3.0) * (cx0 - x);
        let cp2y = y + (2.0 / 3.0) * (cy0 - y);
        self.cubic([cp1x, cp1y, cp2x, cp2y, x, y]);
    }

    fn curve_to(&mut self, cx0: f32, cy0: f32, cx1: f32, cy1: f32, x: f32, y: f32) {
        self.cubic([cx0, cy0, cx1, cy1, x, y]);
    }

    fn close(&mut self) {
        self.push(Command::ClosePath, [0.0; 6]);
        self.current = self.contour_start;
    }
}

#[derive(Clone, Copy)]
#[repr(u8)]
enum Command {
    MoveTo = 1,
    LineTo = 2,
    CurveTo = 3,
    ClosePath = 4,
    End = 5,
}
