# Git リポジトリからのフォント取得

<!-- markdownlint-disable MD013 -->

`FontRepo` を使うと、任意の Git リポジトリをローカルへ同期し、フォントファイルを Dataset として扱えます。

## 基本形

```python
from torchfont.datasets import FontRepo

dataset = FontRepo(
    root="data/fortawesome/font-awesome",
    url="https://github.com/FortAwesome/Font-Awesome",
    ref="7.x",
    patterns=("otfs/*.otf",),
    download=True,
)

print(dataset.commit_hash)
print(len(dataset), len(dataset.style_classes), len(dataset.content_classes))
```

## `FontRepo` を使う判断基準

- 既存 OSS のフォント資産を直接使いたい
- コミットハッシュ固定で再現性を確保したい
- Google Fonts 以外の配布元を統一フローで扱いたい

## `patterns` の書き方

`patterns` は gitignore 互換のマッチングです。

| パターン     | 意味                                                       |
| ------------ | ---------------------------------------------------------- |
| `*.ttf`      | ファイル名ベースで `.ttf` を一致（サブディレクトリを含む） |
| `**/*.ttf`   | 深さを明示した再帰マッチ                                   |
| `otfs/*.otf` | `otfs/` 直下の `.otf`                                      |
| `!*Bold*`    | `Bold` を含むパスを除外                                    |

::: info
`patterns` は候補パスを絞るための条件です。最終的には TorchFont 側で `.ttf` / `.otf` / `.ttc` / `.otc` 拡張子だけが読み込み対象になります。
:::

## 実例

### Font Awesome

```python
FontRepo(
    root="data/fortawesome/font-awesome",
    url="https://github.com/FortAwesome/Font-Awesome",
    ref="7.x",
    patterns=("otfs/*.otf",),
    download=True,
)
```

### Material Design Icons

```python
FontRepo(
    root="data/google/material_design_icons",
    url="https://github.com/google/material-design-icons",
    ref="master",
    patterns=("variablefont/*.ttf",),
    download=True,
)
```

### Source Han Sans (TTC を含む)

```python
FontRepo(
    root="data/adobe-fonts/source-han-sans",
    url="https://github.com/adobe-fonts/source-han-sans",
    ref="release",
    patterns=("*.ttf.ttc",),
    download=True,
)
```

::: info
`*.ttf.ttc` パターンは意図的です。このリポジトリには `Something.ttf.ttc` のような命名の TTC ファイルが含まれます。
:::

## `download` の使い分け

- `download=True`: リモート fetch を実行し、`ref` を force checkout
- `download=False`: fetch を省略し、ローカルで `ref` を解決して force checkout
  （ローカルで解決可能な `ref` が必要）

`root/.git` がない初回は、TorchFont が先にリポジトリ情報を初期化します。それでも `download=False` のままではローカル `ref` が不足して失敗します。

## 重要: 2回目以降は `root` 側の Git リポジトリが優先される

`root` に `.git` がない初回のみ、引数 `url` を使って `origin` を初期化します。

`root/.git` がすでにある場合は、その既存リポジトリを再利用します。このとき `url` を変更しても、同じ `root` の取得元は切り替わりません。

::: warning
どちらのモードでも `root` は force checkout されます。`root` はキャッシュ用途に限定し、ローカル編集を混在させないでください。
:::

::: tip 運用のコツ

- 再現実験では `commit_hash` を保存し、次回は `ref=<保存したハッシュ>`
  で実行してください。
- 同じ `root` での初回実行は `download=True` から始めてください。
- 取得元ごとに `root` を分けて運用してください。

:::

## DataLoader への接続

`FontRepo` は `FontFolder` 継承なので、[DataLoader との統合](/ja/guide/dataloader)と同じ `collate_fn` をそのまま使えます。
