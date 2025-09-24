import streamlit as st
import DataAccess as da
import pandas as pd
from dotenv import load_dotenv
import os
from streamlit_oauth import OAuth2Component

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 環境変数から秘密情報を取得 ---
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# --- Google OAuth2 エンドポイント ---
AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
# REVOKE_ENDPOINT はこのライブラリのバージョンでは使用しないため削除

# --- 画面設定 ---
st.set_page_config(
    page_title="大学受験出願補助アプリ",
    layout="wide"
)

# --- セッション状態の初期化 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_id' not in st.session_state:
    st.session_state.login_id = 0
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# --- 秘密情報が設定されているか確認 ---
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    st.error("`.env`ファイルに `GOOGLE_CLIENT_ID` と `GOOGLE_CLIENT_SECRET` の設定が必要です。")
    st.stop()

# --- OAuth2コンポーネントの作成 ---
# エラーの原因である revoke_endpoint の指定を削除しました
oauth2 = OAuth2Component(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_endpoint=AUTHORIZE_ENDPOINT,
    token_endpoint=TOKEN_ENDPOINT,
    refresh_token_endpoint=None,
)

# --- ログイン状態の確認と処理 ---
if not st.session_state.logged_in:
    # ログインボタンを表示する前にタイトルなどを表示
    st.title("大学受験出願補助アプリ")
    st.info("Googleアカウントでログインしてください。")
    
    result = oauth2.authorize_button(
        name="Googleでログイン",
        icon="https://www.google.com/favicon.ico",
        redirect_uri="http://localhost:8501", # Streamlitの実行URIに合わせて変更
        scope="openid email profile",
        key="google_login",
        use_container_width=True
    )

    if result and "token" in result:
        # === デバッグここから ===
        # Googleから返ってきた情報を画面に表示して確認します
        st.subheader("デバッグ情報：Googleからの応答")
        st.json(result)
        # === デバッグここまで ===

        # 安全にユーザー情報を取得する
        token = result.get("token")
        if token:
            user_info = token.get('userinfo')
            if user_info:
                email = user_info.get('email')
                name = user_info.get('name')
                
                # ユーザー情報をDBに登録/確認し、Login IDを取得
                login_id = da.get_or_create_user_login_id(email, name)
                
                if login_id > 0:
                    st.session_state.logged_in = True
                    st.session_state.login_id = login_id
                    st.session_state.user_name = name
                    st.rerun() # 画面を再読み込みしてメインコンテンツを表示
            else:
                st.error("Googleからの応答にユーザー情報（userinfo）が含まれていませんでした。")
        else:
            st.error("Googleからの応答に認証トークン（token）が含まれていませんでした。")

else:
    # --- ログイン後のヘッダー ---
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title("大学受験出願補助アプリ")
        st.caption(f"ようこそ、{st.session_state.user_name}さん")
    with header_col2:
        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.session_state.login_id = 0
            st.session_state.user_name = ""
            st.rerun()

    st.divider()

    # --- ページ管理 ---
    if 'page' not in st.session_state:
        st.session_state.page = "タスク一覧"

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
    
    # --- コンテンツ表示 ---
    login_id = st.session_state.login_id

    if st.session_state.page == "タスク一覧":
        st.header("タスク一覧")
        st.write("ここでは、出願に必要なタスクを一覧で確認・管理できます。")

        tasks_df = da.get_tasks_by_login_id_from_supabase(login_id)

        if tasks_df.empty:
            st.warning("表示するタスクがありません。まずは「大学追加」画面から受験する大学を登録してください。")
        else:
            st.subheader("表示設定")
            filter_col1, filter_col2, sort_col = st.columns([1, 1, 2])
            with filter_col1:
                show_incomplete = st.checkbox("未完了のみ表示", value=True)
            with filter_col2:
                show_favorite = st.checkbox("お気に入りのみ表示")
            with sort_col:
                sort_key = st.selectbox("並び替え", ("期日が近い順", "大学名順"), index=0, label_visibility="collapsed")
            
            st.divider()

            display_df = tasks_df.copy()
            if show_incomplete:
                display_df = display_df[display_df['ステータス'] == False]
            if show_favorite:
                display_df = display_df[display_df['お気に入り'] == True]

            if sort_key == "期日が近い順":
                display_df['sort_key'] = pd.to_numeric(display_df['期日までの日数'], errors='coerce')
                display_df = display_df.sort_values(by='sort_key', ascending=True, na_position='last').drop(columns=['sort_key'])
            elif sort_key == "大学名順":
                display_df = display_df.sort_values(by=["大学名", "Task ID"], ascending=True)
            
            edited_df = st.data_editor(
                display_df[['ステータス', 'お気に入り', '大学名', 'タスク内容', '期日', '期日までの日数']],
                use_container_width=True,
                column_config={
                    "ステータス": st.column_config.CheckboxColumn("完了", default=False),
                    "お気に入り": st.column_config.CheckboxColumn("⭐", default=False),
                    "期日": st.column_config.DateColumn("期日", format="YYYY/MM/DD"),
                },
                hide_index=True,
                key="task_editor"
            )

    elif st.session_state.page == "スケジュール":
        st.header("スケジュール")
        st.info("（ここにスケジュールカレンダーが表示される予定です）")

    elif st.session_state.page == "大学追加":
        st.header("大学追加")
        unregistered_universities = da.get_unregistered_universities(login_id)

        if not unregistered_universities:
            st.success("全ての大学が追加済みです。")
        else:
            selected_university = st.selectbox(
                "追加する大学を選択してください",
                unregistered_universities,
                index=None,
                placeholder="大学名を選択..."
            )
            if st.button("この大学のタスクを追加する", type="primary"):
                if selected_university:
                    success = da.add_university_tasks_to_supabase(login_id, selected_university)
                    if success:
                        st.success(f"「{selected_university}」のタスクを追加しました。")
                        st.rerun()
                    else:
                        st.error("タスクの追加に失敗しました。")
                else:
                    st.warning("大学を選択してください。")

