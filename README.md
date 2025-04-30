# DRSorter

このスクリプトはDaVinci Resolve Scripting APIを使用し縦写真と横写真をそれぞれ別のタイムラインに振り分けます。

[VerticalHorizontalSorter](https://github.com/a-tak/VerticalHorizontalSorter)の Python移植機能拡張版になります。

## インストール

Pythonファイルを所定の場所に置いてください。

置く場所はDaVinci Resolveの `ヘルプ` > `ドキュメンテーション` > `デベロッパー` から辿って、`Scripting`のフォルダの中の`README.txt`に記載されています。OSによって配置場所が違います。

## 設定

設定は`config.yaml`ファイルで管理します。サンプルの設定ファイル`config.sample.yaml`を`config.yaml`としてコピーし、必要に応じて設定を変更してください。

### 共通設定（common）

- `still_type`: メディアプール内のタイプが画像のクリップを抽出するための名前です。日本語環境では"スチル"、英語環境では"Still"等に設定してください。
- `rotation_angle`: 縦写真のDNGを回転する角度を指定します。デフォルトは90度です。

### デフォルト設定（default）

カメラやレンズ設定のどれにも当てはまらない場合に適用される設定です。
指定しなくてもよいです。

- `power_grade`: デフォルトで適用するパワーグレード（DRX形式）のパスを指定します。DRXファイルはスチルの書き出しの形式をdrxにして書き出すことで作成できます。
- `distortion`: デフォルトのレンズ補正値を指定します。

### アスペクト比別設定（aspect_ratios）

写真のアスペクト比に応じて異なるスケール調整値を設定できます。

例：
```yaml
aspect_ratios:
  "4:3":
    portrait_scale: 1.374  # 4:3の縦写真用スケール値
  "3:2":
    portrait_scale: 1.51   # 3:2の縦写真用スケール値
```

横写真の場合は常にスケール値1.0が適用されます。

### カメラ機種別設定（cameras）

カメラモデルごとに異なるパワーグレードを適用できます。カメラモデル名はDaVinci Resolveのカメラタイムコードの種類(Camera TC Type)の値を使用します。

カメラタイムコードの種類は、DaVinci Resolveのメディアページで扱いたいカメラのJPGファイルを選ぶと右のメタデータに表示されます。表示されていない場合は右上の下向き矢印のボタンから `カメラ` を選んでください。

例：
```yaml
cameras:
  "DC-GH7":
    power_grade: "D:/DaVinci Resolve/PowerGrade/GH7 Normalize.drx"
```

### レンズ別設定（lenses）

レンズごとに異なるDistortion値を設定できます。レンズ名はDaVinci Resolveのレンズの種類(Lens Type)の値を使用します。

確認方法は前項[カメラ機種別設定](#カメラ機種別設定cameras) と同じです。

例：
```yaml
lenses:
  "OLYMPUS M.17mm F1.8":
    distortion: 0.13
```

## 実行方法

対象のビンを開いた状態でメニューの`ワークスペース` > `スクリプト`から実行してください。

## 制限事項

* スクリプトの実行はDaVinci Resolve Studio版が必要になります
* 同じビンにJPGとDNGが配置されている必要があります
  * JPGのメタデータから各種判定するのでDNGだけだと動作しません
* RAWファイルのクリップ名は拡張子部分がDNGまたはdngである必要があります
* 縦写真のDNGファイルの回転方向は固定。現在は左に90度回転するようにしています

## ログ出力

スクリプトの実行状況は以下のようなログ形式で出力されます。
`ワークスペース` > `コンソール` で確認できます。

```
2025-04-28 18:36:52 - INFO - DRXファイルを適用: example.dng
2025-04-28 18:36:52 - WARNING - メディアアイテムが見つかりません
2025-04-28 18:36:52 - ERROR - DRXの適用に失敗: D:\example.drx
```

ログレベルは以下の種類があります：
- INFO: 通常の処理状況
- WARNING: 警告（処理は継続可能）
- ERROR: エラー（一部の処理が失敗）
- CRITICAL: 重大なエラー（処理を継続できない）
