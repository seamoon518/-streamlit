import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, timedelta, timezone

# --- Supabaseの接続情報 ---
# StreamlitのSecrets管理機能を使うか、環境変数から取得することを推奨します。
# ローカルでテストする際は、以下に直接キーを貼り付けても動作します。
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")

# --- Supabaseクライアントの初期化 ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabaseクライアントの初期化エラー: {e}")
    supabase = None

# --- JSTタイムゾーンの定義 ---
JST = timezone(timedelta(hours=+9), 'JST')

# --- (認証関連の関数 sign_up_user, login_user は削除しました) ---

def get_tasks_from_supabase() -> pd.DataFrame:
    """Supabaseからタスク一覧を返す (Login ID 1 に固定)"""
    login_id = 1 # ユーザーを1に固定
    if not supabase: return pd.DataFrame()
    try:
        task_table_data = supabase.from_('タスクテーブル').select('*').eq('"Login ID"', login_id).execute()
        task_master_data = supabase.from_('タスクマスターテーブル').select('*').execute()
        university_master_data = supabase.from_('大学名マスターテーブル').select('*').execute()
        due_date_master_data = supabase.from_('日付マスターテーブル').select('*').execute()
        user_tasks_df = pd.DataFrame(task_table_data.data)
        if user_tasks_df.empty:
            return pd.DataFrame()
        task_master_df = pd.DataFrame(task_master_data.data)
        university_master_df = pd.DataFrame(university_master_data.data)
        due_date_master_df = pd.DataFrame(due_date_master_data.data)
        merged_df = pd.merge(user_tasks_df, task_master_df, on="Task ID", how="left")
        merged_df = pd.merge(merged_df, university_master_df, on="University ID", how="left")
        merged_df = pd.merge(merged_df, due_date_master_df, on="University ID", how="left")
        # 列名を新しいものに合わせて修正 ("Stateu Flag" -> "Status Flag")
        merged_df = merged_df.rename(columns={"Status Flag": "ステータス", "Favorite Flag": "お気に入り", "University Name": "大学名", "Task Name": "タスク内容", "Due Date": "期日"})
        merged_df['期日'] = pd.to_datetime(merged_df['期日'], errors='coerce').dt.date
        today = datetime.now(JST).date()
        merged_df['期日までの日数'] = merged_df['期日'].apply(lambda x: (x - today).days if pd.notna(x) and x >= today else '期限切れ' if pd.notna(x) else '')
        return merged_df
    except Exception as e:
        print(f"タスク取得エラー: {str(e)}")
        return pd.DataFrame()

def update_task_status(task_id: int, status: bool):
    """タスクのステータスを更新"""
    if not supabase: return
    try:
        # 列名を新しいものに合わせて修正 ("Stateu Flag" -> "Status Flag")
        supabase.from_('タスクテーブル').update({'Status Flag': status}).eq('"Task ID"', task_id).execute()
    except Exception as e:
        print(f"ステータス更新エラー: {str(e)}")

def update_task_favorite(task_id: int, favorite: bool):
    """タスクのお気に入りを更新"""
    if not supabase: return
    try:
        # 列名を新しいものに合わせて修正
        supabase.from_('タスクテーブル').update({'Favorite Flag': favorite}).eq('"Task ID"', task_id).execute()
    except Exception as e:
        print(f"お気に入り更新エラー: {str(e)}")

def add_university_tasks_to_supabase(university_name: str) -> bool:
    """大学の全タスクをタスクテーブルに追加 (Login ID 1 に固定)"""
    login_id = 1 # ユーザーを1に固定
    if not supabase: return False
    try:
        uni_res = supabase.from_('大学名マスターテーブル').select('"University ID"').eq('"University Name"', university_name).single().execute()
        university_id = uni_res.data['University ID']
        tasks_res = supabase.from_('タスクマスターテーブル').select('"Task ID"').execute()
        tasks = tasks_res.data
        # 列名を新しいものに合わせて修正 ("Stateu Flag" -> "Status Flag")
        new_tasks = [{"Login ID": login_id, "University ID": university_id, "Task ID": task['Task ID'], "Status Flag": False, "Favorite Flag": False} for task in tasks]
        supabase.from_('タスクテーブル').insert(new_tasks).execute()
        return True
    except Exception as e:
        print(f"大学タスク追加エラー: {str(e)}")
        return False

def get_unregistered_universities() -> list:
    """まだ登録していない大学名の一覧を取得 (Login ID 1 に固定)"""
    login_id = 1 # ユーザーを1に固定
    if not supabase: return []
    try:
        registered_ids_response = supabase.from_('タスクテーブル').select('"University ID"').eq('"Login ID"', login_id).execute()
        registered_ids = {item['University ID'] for item in registered_ids_response.data}
        university_master_response = supabase.from_('大学名マスターテーブル').select('*').execute()
        university_master_df = pd.DataFrame(university_master_response.data)
        if university_master_df.empty:
            return []
        unregistered_df = university_master_df[~university_master_df['University ID'].isin(registered_ids)]
        return unregistered_df['University Name'].tolist()
    except Exception as e:
        print(f"未登録大学取得エラー: {str(e)}")
        return []

