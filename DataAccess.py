import pandas as pd
from supabase import create_client, Client
import os

# --- Supabaseの接続情報 ---
# 環境変数から取得するか、直接指定してください。
# 例: SUPABASE_URL = "https://your-project-id.supabase.co"
# 例: SUPABASE_KEY = "your-anon-key"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")


################################
## タスク一覧を取得する関数
################################

def get_tasks_by_login_id_from_supabase(login_id: int) -> pd.DataFrame:
    """
    Supabaseからデータを取得し、指定した Login ID のタスク一覧を返します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 各テーブルからデータを取得
        task_table_data = supabase.from_('タスクテーブル').select('*').eq('Login ID', login_id).execute()
        task_master_data = supabase.from_('タスクマスターテーブル').select('*').execute()
        university_master_data = supabase.from_('大学名マスターテーブル').select('*').execute()
        due_date_master_data = supabase.from_('日付マスターテーブル').select('*').execute()

        # データをpandas DataFrameに変換
        user_tasks = pd.DataFrame(task_table_data.data)
        task_master = pd.DataFrame(task_master_data.data)
        university_master = pd.DataFrame(university_master_data.data)
        due_date_master = pd.DataFrame(due_date_master_data.data)

    except Exception as e:
        print(f"データの取得中にエラーが発生しました: {e}")
        return pd.DataFrame() # エラー時は空のDataFrameを返す

    # 指定された Login ID のデータがない場合は、空のデータフレームを返します
    if user_tasks.empty:
        print(f"Login ID {login_id} のタスクは見つかりませんでした。")
        return pd.DataFrame(columns=['University Name', 'Task Name', 'University ID', 'Task ID', 'Due date', 'Status Flag', 'Favorite Flag'])

    # 各テーブルと結合して必要な情報を取得します
    # 1. 大学名マスターテーブルと結合
    df = pd.merge(user_tasks, university_master, on='University ID', how='left')

    # 2. タスクマスターテーブルと結合
    df = pd.merge(df, task_master, on='Task ID', how='left')

    # 3. 日付マスターテーブルと結合
    df = pd.merge(df, due_date_master, on=['University ID', 'Task ID'], how='left')

    # 必要な列だけを抽出して新しいデータフレームを作成します
    result_df = df[['University Name', 'Task Name', 'University ID', 'Task ID', 'Due date', 'Status Flag', 'Favorite Flag']]

    return result_df

################################
## タスクのステータスを変更する関数
################################

def update_task_status(login_id: int, university_id: int, task_id: int, new_status: bool) -> dict:
    """
    タスクテーブルの指定されたタスクのStatus Flagを更新します。

    Args:
        login_id (int): 更新したいタスクの Login ID。
        university_id (int): 更新したいタスクの University ID。
        task_id (int): 更新したいタスクの Task ID。
        new_status (bool): 変更後のStatus Flagの値 (True/False)。

    Returns:
        dict: 更新結果を含む辞書。成功した場合は更新されたレコードのリスト、
              失敗した場合はエラー情報。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # データベースを更新
        response = supabase.from_('タスクテーブル').update(
            {'Status Flag': new_status}
        ).eq('Login ID', login_id
        ).eq('University ID', university_id
        ).eq('Task ID', task_id
        ).execute()

        # 更新が成功したか確認
        if response.data:
            print(f"タスク (Login ID: {login_id}, University ID: {university_id}, Task ID: {task_id}) のステータスを {new_status} に更新しました。")
            return {"status": "success", "data": response.data}
        else:
            print(f"指定されたタスクが見つからないか、更新に失敗しました。")
            return {"status": "failure", "error": "No matching task found or update failed."}
            
    except Exception as e:
        print(f"タスクの更新中にエラーが発生しました: {e}")
        return {"status": "error", "error": str(e)}


################################
## タスクのお気に入りを変更する関数
################################

def update_task_status(login_id: int, university_id: int, task_id: int, new_favorite: bool) -> dict:
    """
    タスクテーブルの指定されたタスクのfavorite Flagを更新します。

    Args:
        login_id (int): 更新したいタスクの Login ID。
        university_id (int): 更新したいタスクの University ID。
        task_id (int): 更新したいタスクの Task ID。
        new_favorite (bool): 変更後のFavorite Flagの値 (True/False)。

    Returns:
        dict: 更新結果を含む辞書。成功した場合は更新されたレコードのリスト、
              失敗した場合はエラー情報。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # データベースを更新
        response = supabase.from_('タスクテーブル').update(
            {'Favorite Flag': new_favorite}
        ).eq('Login ID', login_id
        ).eq('University ID', university_id
        ).eq('Task ID', task_id
        ).execute()

        # 更新が成功したか確認
        if response.data:
            print(f"タスク (Login ID: {login_id}, University ID: {university_id}, Task ID: {task_id}) のステータスを {new_favorite} に更新しました。")
            return {"favorite": "success", "data": response.data}
        else:
            print(f"指定されたタスクが見つからないか、更新に失敗しました。")
            return {"favorite": "failure", "error": "No matching task found or update failed."}
            
    except Exception as e:
        print(f"タスクの更新中にエラーが発生しました: {e}")
        return {"favorite": "error", "error": str(e)}


################################
## タスクを新規登録する関数
################################
def add_tasks_for_user(login_id: int, university_id: int) -> dict:
    """
    指定された大学の全タスクをユーザーのタスクテーブルに追加します。

    Args:
        login_id (int): タスクを追加するユーザーの Login ID。
        university_id (int): タスクを追加する大学の University ID。

    Returns:
        dict: 処理結果を含む辞書。成功した場合は追加されたレコードのリスト、
              失敗した場合はエラー情報。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. タスクマスターテーブルから全てのTask IDを取得
        task_master_data = supabase.from_('タスクマスターテーブル').select('Task ID').execute()
        if not task_master_data.data:
            return {"status": "failure", "error": "タスクマスターテーブルにデータがありません。"}

        task_ids_to_add = [task['Task ID'] for task in task_master_data.data]

        # 2. タスクテーブルに挿入するデータを準備
        tasks_to_insert = []
        for task_id in task_ids_to_add:
            tasks_to_insert.append({
                "Login ID": login_id,
                "University ID": university_id,
                "Task ID": task_id,
                "Status Flag": False,
                "Favorite Flag": False
            })

        # 3. データベースに一括挿入
        response = supabase.from_('タスクテーブル').insert(tasks_to_insert).execute()

        # 挿入が成功したか確認
        if response.data:
            print(f"Login ID: {login_id} に University ID: {university_id} のタスクを {len(response.data)} 件追加しました。")
            return {"status": "success", "data": response.data}
        else:
            print(f"タスクの追加に失敗しました。")
            return {"status": "failure", "error": "Insertion failed."}
            
    except Exception as e:
        print(f"タスクの追加中にエラーが発生しました: {e}")
        return {"status": "error", "error": str(e)}



################################
## 未登録の大学名を取得する関数
################################

def get_unregistered_universities() -> list:
    """
    タスクテーブルにまだタスクが登録されていない大学名の一覧を取得します。

    Returns:
        list: 未登録の大学名のリスト。
              エラーが発生した場合は空のリストを返します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. タスクテーブルから登録済みのUniversity IDのユニークなリストを取得
        registered_ids_response = supabase.from_('タスクテーブル').select('"University ID"').execute()
        registered_ids = [item['University ID'] for item in registered_ids_response.data]

        # 2. 大学名マスターテーブルの全データを取得
        university_master_response = supabase.from_('大学名マスターテーブル').select('*').execute()
        university_master_df = pd.DataFrame(university_master_response.data)

        # 3. 登録済みIDのセットを作成して比較を効率化
        registered_id_set = set(registered_ids)
        
        # 4. 未登録のUniversity IDを特定
        unregistered_universities_df = university_master_df[
            ~university_master_df['University ID'].isin(registered_id_set)
        ]
        
        # 5. 未登録の大学名リストを抽出して返す
        unregistered_names = unregistered_universities_df['University Name'].tolist()
        
        if not unregistered_names:
            print("未登録の大学は見つかりませんでした。")
        else:
            print("未登録の大学名が見つかりました。")

        return unregistered_names
            
    except Exception as e:
        print(f"データの取得中にエラーが発生しました: {e}")
        return []
