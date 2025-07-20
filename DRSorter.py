#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import time # timeモジュールをインポート
from datetime import datetime
from typing import Optional, Dict, Any

# PyYAMLのインポートチェック
try:
    import yaml
except ImportError:
    logging.error("PyYAMLがインストールされていません。'pip install pyyaml'を実行してください。")
    raise

import DaVinciResolveScript as dvr_script

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    """設定管理クラス"""
    def __init__(self, config_path: str = "config.yaml"):
        # カレントディレクトリを基準にパスを解決
        self.config_path = os.path.abspath(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            if not os.path.exists(self.config_path):
                logging.warning(f"設定ファイルが見つかりません: {self.config_path} (絶対パス: {os.path.abspath(self.config_path)})")
                return {"default": {}, "cameras": {}, "lenses": {}}
            
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data is None:
                        logging.warning("設定ファイルが空です")
                        return {"default": {}, "cameras": {}, "lenses": {}}
                    return config_data
            except yaml.YAMLError as e:
                logging.error(f"YAMLファイルの解析に失敗: {str(e)}")
                return {"default": {}, "cameras": {}, "lenses": {}}
        except Exception as e:
            logging.error(f"設定ファイルの読み込みに失敗: {str(e)}")
            logging.error(f"現在の作業ディレクトリ: {os.getcwd()}")
            logging.error(f"設定ファイルの絶対パス: {os.path.abspath(self.config_path)}")
            return {"default": {}, "cameras": {}, "lenses": {}}

    def get_power_grade_path(self, camera_type: Optional[str]) -> Optional[str]:
        """カメラタイプに応じたPowerGradeのパスを取得"""
        if camera_type and camera_type in self.config.get('cameras', {}):
            path = self.config['cameras'][camera_type].get('power_grade')
            logging.info(f"カメラ {camera_type} のPowerGrade: {path}")
            return path
        logging.info(f"カメラ {camera_type} の設定が見つからないためデフォルト使用")
        return self.config.get('default', {}).get('power_grade')

    def get_distortion(self, lens_type: Optional[str]) -> float:
        """レンズタイプに応じたDistortion値を取得"""
        if lens_type and lens_type in self.config.get('lenses', {}):
            return self.config['lenses'][lens_type].get('distortion', 0)
        return self.config.get('default', {}).get('distortion', 0)

    def get_still_type(self) -> str:
        """共通設定からスチルタイプを取得"""
        return self.config.get('common', {}).get('still_type', "スチル")

    def get_rotation_angle(self) -> float:
        """共通設定から回転角度を取得"""
        return self.config.get('common', {}).get('rotation_angle', 90.0)
    
    def should_force_color_settings(self) -> bool:
        """カラー設定を強制するかどうかを取得"""
        return self.config.get('color_management', {}).get('force_settings', False)
    
    def get_color_setting(self, setting_name: str) -> Optional[str]:
        """カラー設定の値を取得"""
        color_mgmt = self.config.get('color_management', {})
        setting_map = {
            'colorScienceMode': 'color_science_mode',
            'rcmPresetMode': 'rcm_preset_mode', 
            'colorSpaceOutput': 'color_space_output',
            'colorSpaceInput': 'color_space_input',
            'colorSpaceInputGamma': 'color_space_input_gamma'
        }
        config_key = setting_map.get(setting_name)
        if config_key:
            return color_mgmt.get(config_key)
        return None

def get_resolve():
    """DaVinci Resolveのインスタンスを取得"""
    try:
        resolve = dvr_script.scriptapp("Resolve")
        if not resolve:
            raise Exception("DaVinci Resolveに接続できません")
        return resolve
    except Exception as e:
        logging.critical(f"Resolveの取得に失敗: {str(e)}")
        raise

def apply_grade_from_drx_using_graph(item, drx_file_path, grade_mode):
    """DRXファイルを適用する関数"""
    if not drx_file_path:
        logging.error("DRXファイルが指定されていません")
        return False

    try:
        # ノードグラフを取得
        graph = item.GetNodeGraph()
        if not graph:
            logging.error(f"NodeGraphを取得できませんでした: {item.GetName()}")
            return False

        # DRXを適用
        logging.info(f"DRXファイルを適用: {item.GetName()}")
        success = graph.ApplyGradeFromDRX(drx_file_path, grade_mode)
        if not success:
            logging.error(f"DRXの適用に失敗: {drx_file_path}")
            return False
        return True
    except Exception as e:
        logging.error(f"DRX適用中にエラー発生: {str(e)}")
        return False

class MediaItemCache:
    """メディアアイテムとメタデータのキャッシュを管理するクラス"""
    def __init__(self, media_items):
        self.metadata_cache = {}  # ベース名をキーとしたメタデータのキャッシュ
        self.dng_cache = {}      # ベース名をキーとしたDNGアイテムのキャッシュ
        self.jpeg_cache = {}     # ベース名をキーとしたJPEGアイテムのキャッシュ
        self._build_cache(media_items)

    def _build_cache(self, media_items):
        """メディアアイテムのキャッシュを構築"""
        for item in media_items:
            base_name = os.path.splitext(item.GetClipProperty("Clip Name"))[0]
            format_type = item.GetClipProperty("Format")
            
            if format_type == "JPEG":
                self.jpeg_cache[base_name] = item
                # JPEGファイルからメタデータを取得してキャッシュ
                try:
                    camera_type = item.GetMetadata("Camera TC Type")
                    lens_type = item.GetMetadata("Lens Type")
                    
                    # メタデータが取得できない場合はデフォルト値を使用
                    if not camera_type:
                        camera_type = "default"
                        logging.info(f"Camera TC Typeが取得できないためデフォルト使用: {base_name}")
                    if not lens_type:
                        lens_type = "default"
                        logging.info(f"Lens Typeが取得できないためデフォルト使用: {base_name}")
                        
                    self.metadata_cache[base_name] = {
                        "camera_type": camera_type,
                        "lens_type": lens_type
                    }
                    logging.info(f"メタデータをキャッシュ: {base_name} - Camera: {camera_type}, Lens: {lens_type}")
                    
                except Exception as e:
                    logging.error(f"メタデータの取得に失敗: {base_name}, エラー: {str(e)}")
                    # エラー時もデフォルト値を設定
                    self.metadata_cache[base_name] = {
                        "camera_type": "default",
                        "lens_type": "default"
                    }
            
            elif format_type.lower() == "dng":
                self.dng_cache[base_name] = item

    def get_metadata(self, base_name: str) -> Dict[str, Optional[str]]:
        """キャッシュからメタデータを取得"""
        return self.metadata_cache.get(base_name, {"camera_type": None, "lens_type": None})

    def get_dng_and_metadata(self, media_item) -> tuple:
        """メディアアイテムに対応するDNGアイテムとメタデータを取得"""
        base_name = os.path.splitext(media_item.GetClipProperty("Clip Name"))[0]
        dng_item = self.dng_cache.get(base_name)
        metadata = self.get_metadata(base_name)
        return dng_item, metadata

def set_timeline_resolution(project, timeline, width, height, config): # config を引数に追加
    """タイムラインの解像度とカラー設定を設定する"""
    # タイムライン解像度設定
    timeline.SetSetting("useCustomSettings", "1")
    timeline.SetSetting("timelineResolutionWidth", str(width))
    timeline.SetSetting("timelineResolutionHeight", str(height))
    timeline.SetSetting("timelineOutputResolutionWidth", str(width))
    timeline.SetSetting("timelineOutputResolutionHeight", str(height))

    # カラーマネジメント設定の適用
    timeline.SetSetting("isAutoColorManage", "0")
    
    color_settings_to_copy = [
        "colorScienceMode",
        "rcmPresetMode",
        "colorSpaceOutput"
    ]

    logging.info(f"タイムライン '{timeline.GetName()}' にカラー設定を適用しています...")
    
    if config.should_force_color_settings():
        # 設定ファイルの値を強制使用
        logging.info("設定ファイルのカラー設定を強制適用します...")
        all_color_settings_applied = True
        for setting_name in color_settings_to_copy:
            config_value = config.get_color_setting(setting_name)
            if config_value is not None:
                logging.info(f"  設定ファイル '{setting_name}': {config_value}")
                if timeline.SetSetting(setting_name, config_value):
                    logging.info(f"    -> タイムライン設定 '{setting_name}' に適用しました。")
                else:
                    logging.error(f"    -> エラー: タイムライン設定 '{setting_name}' の適用に失敗しました。")
                    all_color_settings_applied = False
            else:
                logging.warning(f"  警告: 設定ファイル '{setting_name}' が設定されていません。スキップします。")
    else:
        # プロジェクト設定を優先使用
        logging.info("プロジェクトのカラー設定を適用します...")
        all_color_settings_applied = True
        for setting_name in color_settings_to_copy:
            project_setting_value = project.GetSetting(setting_name)
            if project_setting_value is not None:
                logging.info(f"  プロジェクト設定 '{setting_name}': {project_setting_value}")
                if timeline.SetSetting(setting_name, project_setting_value):
                    logging.info(f"    -> タイムライン設定 '{setting_name}' に適用しました。")
                else:
                    logging.error(f"    -> エラー: タイムライン設定 '{setting_name}' の適用に失敗しました。")
                    all_color_settings_applied = False
            else:
                logging.warning(f"  警告: プロジェクト設定 '{setting_name}' を取得できませんでした。スキップします。")

    # カラー設定適用後に自動カラーマネジメントを無効化
    if timeline.SetSetting("isAutoColorManage", "0"):
        logging.info("自動カラーマネジメントを無効化しました。")
    else:
        logging.warning("自動カラーマネジメントの無効化に失敗しました。")
    
    # フォールバック: sRGB強制設定
    output_color_space = config.get_color_setting("colorSpaceOutput") if config.should_force_color_settings() else None
    if output_color_space:
        # 設定ファイルで指定された値を試行
        if timeline.SetSetting("colorSpaceOutput", output_color_space):
            logging.info(f"出力カラースペースを設定ファイル値'{output_color_space}'に設定しました。")
        else:
            logging.warning(f"設定ファイル値'{output_color_space}'の設定に失敗しました。")
    else:
        # デフォルトのsRGBバリエーションを試行
        srgb_variants = ["sRGB", "sRGB (D65)", "sRGB D65"]
        for variant in srgb_variants:
            if timeline.SetSetting("colorSpaceOutput", variant):
                logging.info(f"出力カラースペースを強制的に'{variant}'に設定しました。")
                break
        else:
            logging.warning("sRGBの設定に失敗しました。すべての候補で試行しましたが適用されませんでした。")

    if all_color_settings_applied:
        logging.info(f"タイムライン '{timeline.GetName()}' のカラー設定が正常に適用されました。")
    else:
        logging.warning(f"タイムライン '{timeline.GetName()}' の一部カラー設定の適用に失敗またはスキップされました。")

def main():
    try:
        # スクリプトのパスを取得
        script_path = os.path.dirname(os.path.abspath(
            r"C:\Users\atak\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Edit\DRSorter\DRSorter.py"
        ))
        
        # 設定を読み込む
        config = Config(os.path.join(script_path, "config.yaml"))
        
        # Resolveに接続
        resolve = get_resolve()
        project = resolve.GetProjectManager().GetCurrentProject()
        if not project:
            raise Exception("プロジェクトを取得できません")

        media_pool = project.GetMediaPool()
        if not media_pool:
            raise Exception("メディアプールを取得できません")

        folder = media_pool.GetCurrentFolder()
        if not folder:
            raise Exception("現在のフォルダを取得できません")

        media_items = folder.GetClipList()
        if not media_items:
            logging.warning("メディアアイテムが見つかりません")
            return

        # メディアアイテムのキャッシュを初期化
        media_cache = MediaItemCache(media_items)
        
        # 解像度でグループ化
        resolution_groups = {}
        for media_item in media_items:
            if media_item.GetClipProperty("Type") == config.get_still_type():
                format_type = media_item.GetClipProperty("Format")
                if format_type == "JPEG":
                    resolution = media_item.GetClipProperty("Resolution")
                    try:
                        width, height = map(int, resolution.split('x'))
                        if resolution not in resolution_groups:
                            resolution_groups[resolution] = []
                        resolution_groups[resolution].append(media_item)
                        
                        # キャッシュから対応するDNGファイルを取得
                        dng_item, _ = media_cache.get_dng_and_metadata(media_item)
                        if dng_item and dng_item not in resolution_groups[resolution]:
                            resolution_groups[resolution].append(dng_item)
                                    
                    except ValueError as e:
                        logging.error(f"解像度の解析に失敗: {resolution}, エラー: {str(e)}")

        # 解像度ごとにタイムライン作成
        current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        last_timeline = None
        for resolution, items in resolution_groups.items():
            width, height = map(int, resolution.split('x'))
            
            # タイムライン作成
            timeline = media_pool.CreateEmptyTimeline(
                f"#{width}x{height} Photos {current_time}")
            if not timeline:
                raise Exception(f"タイムライン作成に失敗: {width}x{height}")
            
            # タイムラインの解像度設定
            set_timeline_resolution(project, timeline, width, height, config) # config を引数に追加
            
            # クリップ名でソート
            items.sort(key=lambda x: x.GetClipProperty("Clip Name"))
            
            # クリップを追加（重複を避けるため、すでに追加済みのクリップ名を記録）
            project.SetCurrentTimeline(timeline)
            added_clip_names = []
            for item in items:
                clip_name = item.GetClipProperty("Clip Name")
                if clip_name not in added_clip_names:
                    media_pool.AppendToTimeline(item)
                    added_clip_names.append(clip_name)
            
            # タイムラインアイテムの設定
            timeline_items = timeline.GetItemListInTrack("video", 1)
            if timeline_items:
                for item in timeline_items:
                    media_pool_item = item.GetMediaPoolItem()
                    if media_pool_item.GetClipProperty("Format") == "DNG":
                        _, metadata = media_cache.get_dng_and_metadata(media_pool_item)
                        clip_name = media_pool_item.GetClipProperty("Clip Name")
                        logging.info(f"DNGファイル {clip_name} のメタデータ処理開始")
                        
                        power_grade_path = config.get_power_grade_path(metadata["camera_type"])
                        if power_grade_path:
                            if os.path.exists(power_grade_path):
                                logging.info(f"PowerGrade適用開始: {clip_name} -> {power_grade_path}")
                                if not apply_grade_from_drx_using_graph(item, power_grade_path, 0):
                                    logging.error(f"PowerGrade適用失敗: {clip_name}")
                            else:
                                logging.error(f"PowerGradeファイルが存在しません: {power_grade_path}")
                        
                        distortion = config.get_distortion(metadata["lens_type"])
                        
                        # 対応するJPEGファイルから縦横比を計算してスケールを設定
                        base_name = os.path.splitext(media_pool_item.GetClipProperty("Clip Name"))[0]
                        jpeg_item = media_cache.jpeg_cache.get(base_name)
                        
                        if jpeg_item:
                            # JPEGの解像度を取得
                            jpeg_res = jpeg_item.GetClipProperty("Resolution")
                            jpeg_width, jpeg_height = map(int, jpeg_res.split('x'))
                            
                            # DNGの解像度を取得
                            dng_res = media_pool_item.GetClipProperty("Resolution")
                            dng_width, dng_height = map(int, dng_res.split('x'))
                            
                            if jpeg_width > jpeg_height:  # 横写真の場合
                                # 縦写真と同じ統一計算式を使用
                                scale = dng_width / jpeg_width
                            elif jpeg_width < jpeg_height:  # 縦写真の場合
                                # DNGの幅をJPEGの幅で割る統一計算式
                                scale = dng_width / jpeg_width
                                item.SetProperty("RotationAngle", config.get_rotation_angle())
                            else:  # 正方形（1:1アスペクト比）の場合
                                # 回転処理なし、スケール調整のみ
                                # 正方形の場合はDNGをJPEGの解像度に合わせる
                                scale = dng_width / jpeg_width
                            
                            item.SetProperty("ZoomX", scale)
                            item.SetProperty("ZoomY", scale)  # Y軸にも同じスケールを適用
                        else:
                            logging.warning(f"対応するJPEGファイルが見つかりません: {base_name}")
                        
                        if power_grade_path:
                            apply_grade_from_drx_using_graph(item, power_grade_path, 0)
                        if distortion is not None:
                            item.SetProperty("Distortion", distortion)
            
            last_timeline = timeline

        # 最後に作成されたタイムラインをアクティブに
        if last_timeline:
            project.SetCurrentTimeline(last_timeline)
        logging.info("処理が正常に完了しました")

    except Exception as e:
        logging.critical(f"予期せぬエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()
