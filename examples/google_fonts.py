from torchfont.datasets import GoogleFonts

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}")

for i in range(5):
    print(dataset[i])
