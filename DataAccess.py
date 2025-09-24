import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime, timedelta, timezone

# --- Supabaseの接続情報 ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")

# --- Supabaseクライアントの初期化 (一度だけ行う) ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabaseクライアントの初期化エラー: {e}")
    supabase = None

# --- JSTタイムゾーンの定義 ---
JST = timezone(timedelta(hours=+9), 'JST')


def get_or_create_user_login_id(email: str, name: str) -> int:
    """
    Emailを元にユーザーを検索し、存在しない場合は新規作成する。
    最終的にそのユーザーのLogin IDを返す。
    """
    if not supabase: return 0
    try:
        # ユーザーをEmailで検索
        user_res = supabase.from_('ユーザーテーブル').select('"Login ID"').eq('Email', email).single().execute()
        
        # ユーザーが存在する場合、Login IDを返す
        if user_res.data:
            return user_res.data['Login ID']
    
    except Exception as e:
        # .single()はデータがない場合にPostgrestAPIErrorを発生させるため、ここでキャッチして新規作成フローに流す
        print(f"ユーザー検索エラー（新規ユーザーの可能性）: {str(e)}")

    try:
        # ユーザーが存在しない場合、新規作成
        new_user_res = supabase.from_('ユーザーテーブル').insert({
            'Email': email,
            'Name': name
        }).select('"Login ID"').single().execute()
        return new_user_res.data['Login ID']
    
    except Exception as e2:
        print(f"ユーザー新規作成エラー: {str(e2)}")
        return 0


def get_tasks_by_login_id_from_supabase(login_id: int) -> pd.DataFrame:
    """
    Supabaseからデータを取得し、指定した Login ID のタスク一覧を返します。
    """
    if not supabase: return pd.DataFrame()
    try:
        # 各テーブルからデータを取得
        task_table_data = supabase.from_('タスクテーブル').select('*').eq('"Login ID"', login_id).execute()
        task_master_data = supabase.from_('タスクマスターテーブル').select('*').execute()
        university_master_data = supabase.from_('大学名マスターテーブル').select('*').execute()
        due_date_master_data = supabase.from_('日付マスターテーブル').select('*').execute()

        # pandas DataFrameに変換
        user_tasks_df = pd.DataFrame(task_table_data.data)
        task_master_df = pd.DataFrame(task_master_data.data)
        university_master_df = pd.DataFrame(university_master_data.data)
        due_date_master_df = pd.DataFrame(due_date_master_data.data)

        # データが空の場合は空のDataFrameを返す
        if user_tasks_df.empty:
            return pd.DataFrame()

        # テーブルをマージ
        merged_df = pd.merge(user_tasks_df, task_master_df, on="Task ID", how="left")
        merged_df = pd.merge(merged_df, university_master_df, on="University ID", how="left")
        merged_df = pd.merge(merged_df, due_date_master_df, on="University ID", how="left")

        # 必要なカラムを選択・名前変更
        merged_df = merged_df.rename(columns={
            "Status": "ステータス",
            "Favorite": "お気に入り",
            "University Name": "大学名",
            "Task Name": "タスク内容",
            "Due Date": "期日"
        })

        # 日付処理
        merged_df['期日'] = pd.to_datetime(merged_df['期日'], errors='coerce').dt.date
        today = datetime.now(JST).date()
        merged_df['期日までの日数'] = merged_df['期日'].apply(
            lambda x: (x - today).days if pd.notna(x) and x >= today else '期限切れ' if pd.notna(x) else ''
        )
        
        return merged_df

    except Exception as e:
        print(f"タスク取得エラー: {str(e)}")
        return pd.DataFrame()

def update_task_status(task_id: int, status: bool):
    """タスクのステータスを更新"""
    if not supabase: return
    try:
        supabase.from_('タスクテーブル').update({'Status': status}).eq('"Task ID"', task_id).execute()
    except Exception as e:
        print(f"ステータス更新エラー: {str(e)}")

def update_task_favorite(task_id: int, favorite: bool):
    """タスクのお気に入りを更新"""
    if not supabase: return
    try:
        supabase.from_('タスクテーブル').update({'Favorite': favorite}).eq('"Task ID"', task_id).execute()
    except Exception as e:
        print(f"お気に入り更新エラー: {str(e)}")

def add_university_tasks_to_supabase(login_id: int, university_name: str) -> bool:
    """大学の全タスクをタスクテーブルに追加"""
    if not supabase: return False
    try:
        # 大学名からUniversity IDを取得
        uni_res = supabase.from_('大学名マスターテーブル').select('"University ID"').eq('University Name', university_name).single().execute()
        university_id = uni_res.data['University ID']

        # 全タスクマスターを取得
        tasks_res = supabase.from_('タスクマスターテーブル').select('"Task ID"').execute()
        tasks = tasks_res.data

        # 登録用のデータを作成
        new_tasks = [
            {
                "Login ID": login_id,
                "University ID": university_id,
                "Task ID": task['Task ID'],
                "Status": False,
                "Favorite": False
            }
            for task in tasks
        ]

        # データを挿入
        supabase.from_('タスクテーブル').insert(new_tasks).execute()
        return True
    except Exception as e:
        print(f"大学タスク追加エラー: {str(e)}")
        return False

def get_unregistered_universities(login_id: int) -> list:
    """指定されたユーザーがまだ登録していない大学名の一覧を取得"""
    if not supabase: return []
    try:
        # ログインユーザーが登録済みのUniversity IDを取得
        registered_ids_response = supabase.from_('タスクテーブル').select('"University ID"').eq('"Login ID"', login_id).execute()
        registered_ids = {item['University ID'] for item in registered_ids_response.data}

        # 全ての大学マスターを取得
        university_master_response = supabase.from_('大学名マスターテーブル').select('*').execute()
        university_master_df = pd.DataFrame(university_master_response.data)
        
        if university_master_df.empty:
            return []

        # 未登録の大学を絞り込み
        unregistered_df = university_master_df[~university_master_df['University ID'].isin(registered_ids)]
        return unregistered_df['University Name'].tolist()
    except Exception as e:
        print(f"未登録大学取得エラー: {str(e)}")
        return []

