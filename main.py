import streamlit as st
import DataAccess as da # DataAccess.py をインポート
import pandas as pd

# --- 画面設定 ---
st.set_page_config(
    page_title="大学受験出願補助アプリ",
    layout="wide"
)

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

    # --- データ取得 ---
    # ログイン機能は今後のため、ログインIDを1で固定
    login_id = 1
    tasks_df = da.get_tasks_by_login_id_from_supabase(login_id)

    if tasks_df.empty:
        st.warning("表示するタスクがありません。まずは「大学追加」画面から受験する大学を登録してください。")
    else:
        # --- 絞り込みと並び替えUI ---
        st.subheader("表示設定")
        filter_col1, filter_col2, sort_col = st.columns([1, 1, 2])
        with filter_col1:
            show_incomplete = st.checkbox("未完了のみ表示", value=True)
        with filter_col2:
            show_favorite = st.checkbox("お気に入りのみ表示")
        with sort_col:
            sort_key = st.selectbox(
                "並び替え",
                ("期日が近い順", "大学名順"),
                index=0,
                label_visibility="collapsed"
            )
        
        st.divider()

        # --- データ表示のための準備 ---
        display_df = tasks_df.copy()

        # 絞り込み
        if show_incomplete:
            display_df = display_df[display_df['ステータス'] == False]
        if show_favorite:
            display_df = display_df[display_df['お気に入り'] == True]

        # 並び替え
        if sort_key == "期日が近い順":
            display_df['sort_key'] = pd.to_numeric(display_df['期日までの日数'], errors='coerce')
            display_df = display_df.sort_values(by='sort_key', ascending=True, na_position='last').drop(columns=['sort_key'])
        elif sort_key == "大学名順":
            # 大学名、そしてタスクのIDでソートして表示順を安定させる
            display_df = display_df.sort_values(by=["大学名", "Task ID"], ascending=True)
        
        # --- タスク一覧を表示 ---
        # data_editorを使用してインタラクティブなテーブルを作成
        edited_df = st.data_editor(
            display_df[[
                'ステータス', 'お気に入り', '大学名', 'タスク内容', '期日', '期日までの日数'
            ]],
            use_container_width=True,
            column_config={
                "ステータス": st.column_config.CheckboxColumn("完了", default=False),
                "お気に入り": st.column_config.CheckboxColumn("⭐", default=False),
                "期日": st.column_config.DateColumn(
                    "期日",
                    format="YYYY/MM/DD"
                ),
            },
            hide_index=True,
            key="task_editor"
        )

elif st.session_state.page == "スケジュール":
    st.header("スケジュール")
    st.write("出願関連のスケジュールをカレンダー形式で確認できます。")
    st.info("（ここにスケジュールカレンダーが表示される予定です）")

elif st.session_state.page == "大学追加":
    st.header("大学追加")
    st.write("受験する大学や学部を追加登録します。")

    # --- 未登録の大学リストを取得 ---
    unregistered_universities = da.get_unregistered_universities()

    if not unregistered_universities:
        st.success("全ての大学が追加済みです。")
    else:
        # --- 大学選択のUI ---
        selected_university = st.selectbox(
            "追加する大学を選択してください",
            unregistered_universities,
            index=None, # 初期状態では何も選択されていないようにする
            placeholder="大学名を選択..."
        )

        # --- 追加ボタン ---
        if st.button("この大学のタスクを追加する", type="primary"):
            if selected_university:
                # ログイン機能は今後のため、ログインIDを1で固定
                login_id = 1
                success = da.add_university_tasks_to_supabase(login_id, selected_university)

                if success:
                    st.success(f"「{selected_university}」のタスクを追加しました。タスク一覧画面で確認してください。")
                    # 画面をリロードして、大学選択リストを更新する
                    st.rerun()
                else:
                    st.error("タスクの追加に失敗しました。管理者にお問い合わせください。")
            else:
                st.warning("追加する大学を選択してください。")

