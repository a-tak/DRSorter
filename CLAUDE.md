# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

DRSorterは、DaVinci ResolveのScripting APIを使用して、縦写真と横写真を解像度別に自動的にタイムラインに振り分けるPythonスクリプトです。写真データ（JPEG）のメタデータを元に、対応するRAWファイル（DNG）にカメラ別PowerGradeとレンズ別歪み補正を適用します。

## Development Commands

### Dependencies Installation
```bash
pip install -r requirements.txt
```

### Testing
No automated tests - manual testing through DaVinci Resolve interface

### Configuration
- Copy `config.sample.yaml` to `config.yaml` and customize settings
- Configure camera-specific PowerGrade (.drx files) paths
- Set lens-specific distortion values

## Architecture

### Core Components

**DRSorter.py**: メインスクリプト
- `Config`クラス: YAML設定ファイル管理
- `MediaItemCache`クラス: JPEGメタデータとDNGファイルのペア管理
- `set_timeline_resolution()`: タイムライン解像度とカラー設定の適用
- `apply_grade_from_drx_using_graph()`: PowerGrade適用

### Data Flow
1. メディアプール内のJPEG/DNGファイルを解析
2. JPEGファイルからカメラ/レンズメタデータを抽出
3. 解像度グループ別にタイムライン作成
4. DNGファイルにPowerGrade・歪み補正・回転/スケール適用

### Configuration Structure
```yaml
common:
  still_type: "スチル"  # または "Still" (英語環境)
  rotation_angle: 90.0

# カラーマネジメント設定（新機能）
color_management:
  force_settings: false  # true: 設定ファイル値を強制、false: プロジェクト設定優先
  color_science_mode: "davinciYRGBColorManagedv2"
  rcm_preset_mode: "SDR"
  color_space_output: "sRGB"

cameras:
  "Camera Model": 
    power_grade: "path/to/grade.drx"

lenses:
  "Lens Model":
    distortion: 0.13
```

### Color Management Features
- **プロジェクト設定継承**: デフォルトでプロジェクトのカラー設定をタイムラインに適用
- **設定ファイル強制**: `force_settings: true`で固定値を強制適用
- **フォールバック機能**: プロジェクト設定失敗時にsRGBを自動設定

### DaVinci Resolve Integration
- スクリプトは `Scripts/Edit` フォルダに配置
- DaVinci Resolve Studio版が必須（無料版はスクリプティング非対応）
- メディアページで写真ビンを選択後、ワークスペース > スクリプト から実行

### File Relationships
- JPEGとDNGファイルは同一ベース名で対応付け
- JPEGからメタデータ取得、DNGに処理適用
- 縦写真は自動回転+アスペクト比スケール適用