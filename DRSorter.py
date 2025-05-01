#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
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

def set_timeline_resolution(timeline, width, height):
    """タイムラインの解像度を設定する"""
    timeline.SetSetting("useCustomSettings", "1")
    timeline.SetSetting("timelineResolutionWidth", str(width))
    timeline.SetSetting("timelineResolutionHeight", str(height))
    timeline.SetSetting("timelineOutputResolutionWidth", str(width))
    timeline.SetSetting("timelineOutputResolutionHeight", str(height))

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
            set_timeline_resolution(timeline, width, height)
            
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
                            resolution = jpeg_item.GetClipProperty("Resolution")
                            width, height = map(int, resolution.split('x'))
                            if width > height:
                                scale = 1.0  # 横向きは常に1.0
                            else:
                                # JPEGの実際の縦横比から計算（縦写真の場合はheight/width）
                                scale = height / width
                                item.SetProperty("RotationAngle", config.get_rotation_angle())
                            
                            item.SetProperty("ZoomX", scale)
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
