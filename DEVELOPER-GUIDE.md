# Developer Guide

## Requirements

- Python >= 3.13
- [Poetry](https://python-poetry.org/)

## Installation

リポジトリに設置してあるパッケージをパッケージインデックスとして参照するため,
バックグラウンドでファイルサーバを起動しておきます.

```shell
python -m http.server
```

ファイルサーバを起動したら, Poetry でインストールします.

```shell
poetry install
```

## Testing

一部テストで
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
を使用します. アプリ公式ガイドの手順を参考に事前にインストールしてください.
当該テストをスキップする場合, 環境変数に
`NO_TESSERACT=1` を設定してください.

```shell
poetry run pytest
poetry run ruff check .
poetry run mypy .
poetry run black --check .
```

## Build

[cv_Freeze](https://cx-freeze.readthedocs.io/en/stable/)
で配布形式にビルドします. ビルド用の依存パッケージは
`build` グループとしており, デフォルトではインストールされないことに注意してください.

```shell
poetry install --with build
poetry run cxfreeze build_exe
```

## Resources

### Pokémon Database

[PokéAPI](https://pokeapi.co/) から取得しています.
リソースファイル作成コードは
[pokescreader-database](https://github.com/takosavi/pokescreader-database)
で公開しています.

### Terastal

以下の 2 つをデータとして収録しています.

- テラスタイプが分かる直前の画面で用いる画像マスク
- テラスタイプごとに異なる画面の色合い情報

画像ファイル群から学習モデルを作成するコードは同梱していますが,
作成手順はまだ整備しておりません. ごめんなさい.

なお, 学習に用いた画像ファイルを公開する予定はありません.

### Tesseract OCR

#### 日本語モデル

[tessdata_best](https://github.com/tesseract-ocr/tessdata_best/)
の日本語学習モデル (`jpn.traineddata`) を
[ニタラゴルイカ](https://www.type-labo.jp/Hanpunitalago.html)
フォントでファインチューニングしたものを収録しています.
(本当は "ロダンNTLG" がよかったのですが調達できませんでした...)

チューニング方法はまだ整備しておりません. ごめんなさい.

#### 英語モデル

[tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast)
の英語学習モデル (`eng.traineddata`) をそのまま使用しています.
HP や PP など, 数値の読み取りに使用しています.

## Unreleased Codes

このプロジェクトでは未公開のコードがあります.

### pnlib

バイナリパッケージとしてインストールしている `pnlib` は,
諸事情により実装を非公開としています.

`pnlib` に収録している実装は
[ぱにぱにツール](https://www.panipanipanipa.com/entry/2022/12/22/193408)
を参考にしています. 実装を知りたい方は,
作者であるぱにぱに様が公開されている
[【有料記事】ぱにぱにツールSV ver1.2のソースコードと簡単な解説](https://note.com/panipani67/n/n067ff33fee74)
をご参照ください.

### Integration Test

開発中にはゲーム中のスクリーンショットを使った自動結合テストを行っています.
スクリーンショットをリポジトリ上で公開することの是非を判断できていませんので,
現在は個人的な利用の範囲に留めることとし,
当該のテストコードおよびそれに用いるスクリーンショットは非公開としています.
