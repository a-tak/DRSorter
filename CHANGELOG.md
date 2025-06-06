# 変更履歴

## [1.0.0] - 2025-06-02

### 追加
- DaVinci Resolve用写真仕分けスクリプトの初回リリース
- 縦写真と横写真を解像度別にタイムラインに自動振り分け
- JPEGメタデータを使用したカメラ・レンズ別PowerGrade適用
- カメラ別PowerGrade (.drx) ファイル適用機能
- レンズ別歪み補正機能
- 縦写真の自動回転・スケール調整機能
- 柔軟なカラーマネジメント設定（プロジェクト設定継承/強制設定）
- YAML設定ファイルによる詳細なカスタマイズ
- 包括的なログ出力とエラーハンドリング

### 機能詳細
- **解像度グループ化**: 写真を解像度別に自動グループ化してタイムライン作成
- **メタデータ処理**: JPEGファイルからカメラ・レンズ情報を抽出
- **カラー設定**: プロジェクト設定継承またはsRGBフォールバック
- **ファイル対応**: JPEGとDNGファイルのペア処理
- **スケール計算**: 縦写真の適切なアスペクト比維持

### 対応環境
- DaVinci Resolve Studio版
- Python 3.6以上 64bit版
- Windows/macOS/Linux
- 外部スクリプティング有効化必須