import DaVinciResolveScript as dvr_script

# DaVinci Resolveオブジェクトを取得
resolve = dvr_script.scriptapp("Resolve")

if not resolve:
    print("DaVinci Resolveに接続できませんでした。")
    exit()

# プロジェクトマネージャーと現在のプロジェクトを取得
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()

if not project:
    print("現在のプロジェクトを開けませんでした。")
    exit()

# 現在のタイムラインを取得
timeline = project.GetCurrentTimeline()

if not timeline:
    print("現在のタイムラインを取得できませんでした。")
    exit()

# プロジェクトからタイムラインにコピーする設定キーのリスト
settings_to_copy = [
    "colorScienceMode",
    "colorSpaceInput",
    "colorSpaceInputGamma",
    "colorSpaceOutput"
]

print("プロジェクト設定をタイムラインに適用しています...")

all_settings_applied = True

for setting_name in settings_to_copy:
    project_setting_value = project.GetSetting(setting_name)
    if project_setting_value is not None:
        print(f"  プロジェクト設定 '{setting_name}': {project_setting_value}")
        # タイムラインに設定を適用
        # 注意: タイムライン設定のキー名がプロジェクト設定のキー名と完全に一致するとは限りません。
        # ResolveのAPIドキュメントで、対応するタイムライン設定キーを確認してください。
        # ここでは、キー名が同じであると仮定して進めます。
        if timeline.SetSetting(setting_name, project_setting_value):
            print(f"    -> タイムライン設定 '{setting_name}' に適用しました。")
        else:
            print(f"    -> エラー: タイムライン設定 '{setting_name}' の適用に失敗しました。")
            all_settings_applied = False
    else:
        print(f"  警告: プロジェクト設定 '{setting_name}' を取得できませんでした。スキップします。")
        all_settings_applied = False # 取得できない場合も失敗とみなすか、要件による

if all_settings_applied:
    print("すべての指定されたプロジェクト設定がタイムラインに正常に適用されました。")
else:
    print("いくつかの設定の適用に失敗したか、プロジェクトから取得できませんでした。詳細は上記のログを確認してください。")
