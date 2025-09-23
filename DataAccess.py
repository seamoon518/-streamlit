import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime

# --- Supabaseの接続情報 ---
# ファイルの先頭で一度だけクライアントを初期化します
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

################################
## タスク一覧を取得する関数
################################
def get_tasks_by_login_id_from_supabase(login_id: int) -> pd.DataFrame:
    """
    Supabaseからデータを取得し、指定した Login ID のタスク一覧を返します。
    """
    try:
        # 'Task Table ID'も選択して、更新処理で使えるようにします
        task_table_data = supabase.from_('タスクテーブル').select('*, "Task Table ID"').eq('Login ID', login_id).execute()
        task_master_data = supabase.from_('タスクマスターテーブル').select('*').execute()
        university_master_data = supabase.from_('大学名マスターテーブル').select('*').execute()
        due_date_master_data = supabase.from_('日付マスターテーブル').select('*').execute()

        user_task_df = pd.DataFrame(task_table_data.data)
        if user_task_df.empty:
            return pd.DataFrame()

        task_master_df = pd.DataFrame(task_master_data.data)
        university_master_df = pd.DataFrame(university_master_data.data)
        due_date_master_df = pd.DataFrame(due_date_master_data.data)

        merged_df = pd.merge(user_task_df, task_master_df, on='Task ID', how='left')
        merged_df = pd.merge(merged_df, university_master_df, on='University ID', how='left')
        merged_df = pd.merge(merged_df, due_date_master_df, on='Due Date ID', how='left')
        
        if 'Due Date' in merged_df.columns and not merged_df['Due Date'].isnull().all():
            merged_df['Due Date'] = pd.to_datetime(merged_df['Due Date'])
            merged_df['Due Date'] = merged_df['Due Date'].dt.tz_convert('Asia/Tokyo')
            merged_df['Days Until Due'] = (merged_df['Due Date'].dt.date - datetime.now().date()).dt.days
        else:
             merged_df['Days Until Due'] = None

        merged_df = merged_df.rename(columns={
            'University Name': '大学名',
            'Task Name': 'タスク内容',
            'Due Date': '期日',
            'Status': 'ステータス',
            'Favorite': 'お気に入り',
            'Days Until Due': '期日までの日数'
        })

        return merged_df
    except Exception as e:
        print(f"データ取得中にエラーが発生しました: {e}")
        return pd.DataFrame()

################################
## 未登録の大学名を取得する関数
################################
def get_unregistered_universities() -> list:
    """
    タスクテーブルにまだタスクが登録されていない大学名の一覧を取得します。
    """
    try:
        registered_ids_response = supabase.from_('タスクテーブル').select('"University ID"').execute()
        registered_ids = {item['University ID'] for item in registered_ids_response.data}

        university_master_response = supabase.from_('大学名マスターテーブル').select('*').execute()
        university_master_df = pd.DataFrame(university_master_response.data)
        
        unregistered_df = university_master_df[~university_master_df['University ID'].isin(registered_ids)]
        return unregistered_df['University Name'].tolist()
    except Exception as e:
        print(f"未登録大学の取得中にエラーが発生しました: {str(e)}")
        return []

################################
## タスクのステータスを更新する関数
################################
def update_task_status_in_supabase(task_table_id: int, new_status: bool):
    """
    指定されたタスクのステータス（完了/未完了）を更新します。
    """
    try:
        supabase.from_('タスクテーブル').update({'Status': new_status}).eq('Task Table ID', task_table_id).execute()
        return True
    except Exception as e:
        print(f"ステータス更新中にエラーが発生しました: {e}")
        return False

################################
## タスクのお気に入りを更新する関数
################################
def update_task_favorite_in_supabase(task_table_id: int, new_favorite: bool):
    """
    指定されたタスクのお気に入り状態を更新します。
    """
    try:
        supabase.from_('タスクテーブル').update({'Favorite': new_favorite}).eq('Task Table ID', task_table_id).execute()
        return True
    except Exception as e:
        print(f"お気に入り更新中にエラーが発生しました: {e}")
        return False

################################
## 新しい大学のタスクを追加する関数
################################
def add_university_tasks_to_supabase(login_id: int, university_name: str):
    """
    指定された大学の標準タスク一式をユーザーのタスクリストに追加します。
    """
    try:
        # 1. 大学名からUniversity IDを取得
        uni_res = supabase.from_('大学名マスターテーブル').select('University ID').eq('University Name', university_name).single().execute()
        university_id = uni_res.data['University ID']

        # 2. 標準タスクをタスクマスターから全て取得
        task_master_res = supabase.from_('タスクマスターテーブル').select('Task ID').execute()
        task_ids = [task['Task ID'] for task in task_master_res.data]

        # 3. 挿入するデータのリストを作成
        tasks_to_insert = [
            {
                'Login ID': login_id,
                'University ID': university_id,
                'Task ID': task_id,
                'Status': False,
                'Favorite': False
            }
            for task_id in task_ids
        ]

        # 4. タスクテーブルに新しいタスクを一括で挿入
        supabase.from_('タスクテーブル').insert(tasks_to_insert).execute()
        return True
    except Exception as e:
        print(f"大学タスク追加中にエラーが発生しました: {e}")
        return False

