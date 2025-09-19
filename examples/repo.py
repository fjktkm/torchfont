from torchfont.datasets import FontRepo

dataset = FontRepo(
    root="data/source-han-sans",
    url="https://github.com/adobe-fonts/source-han-sans",
    ref="release",
    patterns=["Variable/TTF/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}")

for i in range(5):
    print(dataset[i])
