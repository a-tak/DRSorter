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

# プロジェクトの設定を取得 (例: プロジェクト名)
# 他の設定を取得したい場合は、ここのキーを変更してください。
# 利用可能なキーについては、DaVinci Resolveのスクリプティングドキュメントを参照してください。
setting_name = "projectName"
setting_value = project.GetSetting()

if setting_value is not None:
    print(f"プロジェクト設定 '{setting_name}': {setting_value}")
else:
    print(f"プロジェクト設定 '{setting_name}' を取得できませんでした。")
