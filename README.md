# DRSorter

## 目次
1. [概要](#概要)
2. [前提条件](#前提条件)
3. [インストール手順](#インストール手順)
4. [設定方法](#設定方法)
5. [使用方法](#使用方法)
6. [トラブルシューティング](#トラブルシューティング)
7. [制限事項](#制限事項)
8. [ログ出力](#ログ出力)

## 概要
このスクリプトはDaVinci Resolve Scripting APIを使用し、縦写真と横写真をそれぞれ別のタイムラインに振り分けます。
[VerticalHorizontalSorter](https://github.com/a-tak/VerticalHorizontalSorter)のPython移植機能拡張版です。

## 前提条件
- DaVinci Resolve Studio版（スクリプティング機能は無料版では使用できません）
- Python 3.6以上 64bit版
- スクリプティング権限の設定
  - DaVinci Resolveの環境設定 > 一般 > 外部スクリプティング > 「外部スクリプティングの使用」を有効化

## インストール手順

### 1. 依存パッケージのインストール
必要なパッケージをインストールするには以下のコマンドを実行してください：

```bash
pip install pyyaml
```

または、プロジェクトに含まれるrequirements.txtを使用して：

```bash
pip install -r requirements.txt
```

### 2. Pythonのインストール
1. [Python公式サイト](https://www.python.org/)から64bit版をダウンロード
2. インストーラーを実行
   - 「Add Python to PATH」にチェックを入れることを推奨
   - 「Install for all users」を選択することを推奨

### 2. 環境変数の設定
スクリプトを外部から実行する場合は、以下の環境変数の設定が必要です。

Windows:
```cmd
setx RESOLVE_SCRIPT_API "%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
setx RESOLVE_SCRIPT_LIB "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
setx PYTHONPATH "%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\"
```

Mac OS X:
```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

Linux:
```bash
export RESOLVE_SCRIPT_API="/opt/resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/opt/resolve/libs/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

### 3. スクリプトの配置
スクリプトファイル（DRSorter.py）を以下のフォルダに配置してください：

Windows:
- 全ユーザー: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Edit`
- 個人ユーザー: `%APPDATA%\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Edit`

Mac OS X:
- 全ユーザー: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit`
- 個人ユーザー: `/Users/<UserName>/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit`

Linux:
- 全ユーザー: `/opt/resolve/Fusion/Scripts/Edit`
- 個人ユーザー: `$HOME/.local/share/DaVinciResolve/Fusion/Scripts/Edit`

## 設定方法

設定は`config.yaml`ファイルで管理します。サンプルの設定ファイル`config.sample.yaml`を`config.yaml`としてコピーし、必要に応じて設定を変更してください。

### 共通設定（common）

- `still_type`: メディアプール内のタイプが画像のクリップを抽出するための名前です。日本語環境では"スチル"、英語環境では"Still"等に設定してください。
- `rotation_angle`: 縦写真のDNGを回転する角度を指定します。デフォルトは90度です。

### カラーマネジメント設定（color_management）

タイムライン作成時のカラー設定を詳細に制御できます。設定ファイルで以下のような制御が可能です：

```yaml
color_management:
  force_settings: false  # true: 設定ファイル値を強制、false: プロジェクト設定優先
  color_science_mode: "davinciYRGBColorManagedv2"
  rcm_preset_mode: "SDR"
  color_space_output: "sRGB"  # 出力カラースペース
```

#### 動作モード
- **`force_settings: false`** (デフォルト): プロジェクト設定を継承し、失敗時にsRGBにフォールバック
- **`force_settings: true`**: 設定ファイルで指定した値を強制適用

#### 確実にsRGBを設定したい場合
```yaml
color_management:
  force_settings: true
  color_space_output: "sRGB"
```

### デフォルト設定（default）

カメラやレンズ設定のどれにも当てはまらない場合に適用される設定です。
指定しなくてもよいです。

- `power_grade`: デフォルトで適用するパワーグレード（DRX形式）のパスを指定します。DRXファイルはスチルの書き出しの形式をdrxにして書き出すことで作成できます。
- `distortion`: デフォルトのレンズ補正値を指定します。

### DNGファイルのスケール値の計算

縦構図のDNGファイルは縦方向に回転後ズームをしてタイムライン一杯に広がるようにしています。

縦横写真のスケール値は以下のように計算されます：

- 横写真の場合：常にスケール値1.0が適用されます
- 縦写真の場合：対応するJPEGファイルの縦横比（height/width）が自動的に計算され、スケール値として適用されます
  - 例：3:2の縦写真（2000x3000）の場合、3000/2000 = 1.5がスケール値として使用されます

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

## 使用方法

1. DaVinci Resolveを起動
2. メディアページで対象の写真が含まれるビンを開く
3. メニューの`ワークスペース` > `スクリプト` > `Edit` から`DRSorter`を選択
4. スクリプトが実行され、縦写真と横写真が自動的に振り分けられます

## トラブルシューティング

### よくある問題と解決方法

1. スクリプトが表示されない
   - スクリプトの配置場所が正しいか確認
   - DaVinci Resolveを再起動
   - スクリプティング権限が有効になっているか確認

2. 環境変数エラー
   - 環境変数が正しく設定されているか確認
   - システム環境変数の設定後、PCを再起動

3. Pythonエラー
   - Python 64bit版がインストールされているか確認
   - PYTHONPATHが正しく設定されているか確認

4. DRXファイルが適用されない
   - ファイルパスが正しいか確認
   - DRXファイルが存在するか確認
   - パスに日本語が含まれていないか確認

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
