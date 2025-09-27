import streamlit as st
import pandas as pd # DataFrameを扱うため追加

# DataAccess.pyから必要な関数をインポート
from DataAccess import (
    get_tasks_by_login_id_from_supabase, 
    get_unregistered_universities, 
    add_tasks_for_user,
    update_favorite_status,
    update_task_status
)


# --- 画面設定 ---
st.set_page_config(
    page_title="大学受験出願補助アプリ",
    layout="wide"
)

# --- Streamlitのデータキャッシュ機能を使って、Supabaseからのデータ取得関数を定義 ---
# アプリの再実行時にデータベースからデータを再取得するのを防ぎ、パフォーマンスを向上させます。
@st.cache_data
def load_tasks_data():
    """DataAccessからタスク一覧を取得し、キャッシュする関数"""
    # DataAccess.pyで定義された関数を呼び出す
    return get_tasks_by_login_id_from_supabase()

# --- メイン画面 ---
st.title("大学受験出願補助アプリ")
st.caption("あなたの大学受験をサポートします。")

# --- ページ管理のためのセッション状態を初期化 ---
if 'page' not in st.session_state:
    st.session_state.page = "タスク一覧"

# --- ナビゲーションボタン ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("タスク一覧", use_container_width=True, type="primary" if st.session_state.page == "タスク一覧" else "secondary"):
        st.session_state.page = "タスク一覧"

with col2:
    if st.button("スケジュール", use_container_width=True, type="primary" if st.session_state.page == "スケジュール" else "secondary"):
        st.session_state.page = "スケジュール"

with col3:
    if st.button("大学追加", use_container_width=True, type="primary" if st.session_state.page == "大学追加" else "secondary"):
        st.session_state.page = "大学追加"

st.divider()

# --- 選択されたページに応じてコンテンツを表示 ---
if st.session_state.page == "タスク一覧":
    st.header("タスク一覧")
    st.write("ここでは、出願に必要なタスクを一覧で確認・管理できます。")
    
    # データをロードし、進捗状況を表示
    with st.spinner('タスクデータをロード中...'):
        tasks_df = load_tasks_data() # キャッシュされた関数を呼び出し、タスク一覧を取得
    
    # データの表示
    if not tasks_df.empty:
        # 取得したDataFrameをStreamlitに表示
        st.dataframe(tasks_df, use_container_width=True)
    else:
        # データが空の場合のメッセージ
        st.warning("タスクデータが見つからないか、データベースからのロード中にエラーが発生しました。")


elif st.session_state.page == "スケジュール":
    st.header("スケジュール")
    st.write("出願関連のスケジュールをカレンダー形式で確認できます。")
    # 今後のステップで、ここにカレンダー機能を追加していきます。
    st.info("（ここにスケジュールカレンダーが表示される予定です）")

elif st.session_state.page == "大学追加":
    st.header("大学追加")
    st.write("受験する大学や学部を追加登録します。")
    # 今後のステップで、ここに大学追加フォームを追加していきます。
    st.info("（ここに大学を追加するフォームが表示される予定です）")