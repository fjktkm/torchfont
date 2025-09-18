from torchfont.datasets import FontRepo

dataset = FontRepo(
    root="data/public_sans",
    url="https://github.com/uswds/public-sans",
    ref="develop",
    patterns=["fonts/variable/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/plus_jakarta_sans",
    url="https://github.com/tokotype/PlusJakartaSans",
    ref="master",
    patterns=["fonts/variable/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/open_sauce_fonts",
    url="https://github.com/marcologous/Open-Sauce-Fonts",
    ref="master",
    patterns=["fonts/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/urbanist",
    url="https://github.com/coreyhu/Urbanist",
    ref="main",
    patterns=["fonts/variable/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/inria_fonts",
    url="https://github.com/BlackFoundryCom/InriaFonts",
    ref="master",
    patterns=["fonts/*/OTF/*.otf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/caskaydia_cove",
    url="https://github.com/eliheuer/caskaydia-cove",
    ref="master",
    patterns=["fonts/variable/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/open_relay",
    url="https://github.com/kreativekorp/open-relay",
    ref="master",
    patterns=["*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/hauora_sans",
    url="https://github.com/WCYS-Co/Hauora-Sans",
    ref="master",
    patterns=["fonts/variable/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")

dataset = FontRepo(
    root="data/foundation_titles_hand",
    url="https://github.com/rsperberg/foundation-titles-hand",
    ref="main",
    patterns=["fonts/ttf/latest/*.ttf"],
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}\n")
