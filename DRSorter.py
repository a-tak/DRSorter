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

    def get_portrait_scale(self, lens_type: Optional[str]) -> float:
        """レンズタイプに応じた縦向き写真用のスケール値を取得"""
        if lens_type and lens_type in self.config.get('lenses', {}):
            return self.config['lenses'][lens_type].get('portrait_scale', 
                self.config.get('default', {}).get('portrait_scale', 1.334))
        return self.config.get('default', {}).get('portrait_scale', 1.334)

    def get_landscape_scale(self, lens_type: Optional[str]) -> float:
        """レンズタイプに応じた横向き写真用のスケール値を取得"""
        if lens_type and lens_type in self.config.get('lenses', {}):
            return self.config['lenses'][lens_type].get('landscape_scale', 
                self.config.get('default', {}).get('landscape_scale', 1.0))
        return self.config.get('default', {}).get('landscape_scale', 1.0)

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

def get_metadata_from_jpeg(media_item) -> Dict[str, Optional[str]]:
    """JPEGファイルからメタデータを取得"""
    try:
        camera_type = media_item.GetMetadata("Camera TC Type")
        lens_type = media_item.GetMetadata("Lens Type")
        # デバッグ情報を追加
        logging.info(f"メタデータ取得: Camera TC Type = {camera_type}, Lens Type = {lens_type}")
        if not camera_type:
            logging.warning("Camera TC Typeが取得できませんでした")
        return {
            "camera_type": camera_type,
            "lens_type": lens_type
        }
    except Exception as e:
        logging.error(f"メタデータの取得に失敗: {str(e)}")
        return {"camera_type": None, "lens_type": None}

def get_media_item_by_basename_and_dng(media_item, media_items):
    """同じベース名で拡張子がDNGのmediaItemを取得し、メタデータも返す"""
    try:
        # ベース名を取得
        base_name = os.path.splitext(media_item.GetClipProperty("Clip Name"))[0]
        
        # DNGファイルを検索
        dng_item = None
        jpeg_item = None
        
        # メディアアイテムを分類
        if media_item.GetClipProperty("Format") == "JPEG":
            jpeg_item = media_item
        elif media_item.GetClipProperty("Format").lower() == "dng":
            dng_item = media_item
            
        # 対応するファイルを検索
        for item in media_items:
            item_name = item.GetClipProperty("Clip Name")
            item_base = os.path.splitext(item_name)[0]
            
            if item_base == base_name:
                if item.GetClipProperty("Format") == "JPEG":
                    jpeg_item = item
                elif item.GetClipProperty("Format").lower() == "dng":
                    dng_item = item
        
        # メタデータを取得（常にJPEGから）
        metadata = get_metadata_from_jpeg(jpeg_item) if jpeg_item else {
            "camera_type": None,
            "lens_type": None
        }
        
        return dng_item, metadata
    except Exception as e:
        logging.error(f"DNGファイル検索中にエラー発生: {str(e)}")
        return None, {"camera_type": None, "lens_type": None}

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
                        
                        # 対応するDNGファイルを検索して同じ解像度グループに追加
                        dng_item, _ = get_media_item_by_basename_and_dng(media_item, media_items)
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
                        _, metadata = get_media_item_by_basename_and_dng(media_pool_item, media_items)
                        logging.info(f"DNGファイル {media_pool_item.GetClipProperty('Clip Name')} のメタデータ: {metadata}")
                        
                        power_grade_path = config.get_power_grade_path(metadata["camera_type"])
                        distortion = config.get_distortion(metadata["lens_type"])
                        
                        # 縦横判定して適切なスケールを設定
                        width, height = map(int, resolution.split('x'))
                        if width > height:
                            scale = config.get_landscape_scale(metadata["lens_type"])
                        else:
                            scale = config.get_portrait_scale(metadata["lens_type"])
                            item.SetProperty("RotationAngle", config.get_rotation_angle())
                        
                        item.SetProperty("ZoomX", scale)
                        
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
