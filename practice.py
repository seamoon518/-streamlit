import os
from supabase import create_client, Client

# --- Supabaseの接続情報 (DataAccess.pyから転記) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")

def test_university_master_connection():
    """
    Supabaseの「大学名マスターテーブル」に接続し、データを取得できるかテストします。
    """
    print("--- 大学名マスターテーブルのデバッグ処理を開始します ---")
    
    try:
        # Supabaseクライアントを初期化
        # ★修正点: SUPABASE_key -> SUPABASE_KEY に修正
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("1. Supabaseクライアントの初期化に成功しました。")

        # 「大学名マスターテーブル」から全てのデータを取得
        response = supabase.from_('大学名マスターテーブル').select('*').execute()
        print("2. データの取得を試みました。")

        # 実行結果の確認
        if response.data:
            print(f"3. 成功: {len(response.data)}件のデータを取得しました。")
            print("--- 取得したデータの1件目 ---")
            print(response.data[0])
            print("--------------------------")
        elif len(response.data) == 0:
            print("3. 成功: テーブルに接続できましたが、データは0件です。")
        else:
            print("3. 失敗: データ取得に失敗しました。レスポンス内容を確認してください。")
            print(response)

    except Exception as e:
        print(f"!!! エラーが発生しました: {e}")
        print("SupabaseのURL、KEY、テーブル名、またはRLS(Row Level Security)設定を確認してください。")

    finally:
        print("\n--- デバッグ処理を完了しました ---")

if __name__ == "__main__":
    test_university_master_connection()

