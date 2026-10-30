import ja_contexto_system as game_logic
import flet as ft
from typing import Set, Optional
import math
import sys
import traceback
import os
import datetime

# エラーログをファイルに出力する関数
def log_error(error_msg: str, exception: Exception = None):
    """エラーログをファイルに書き込む"""
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"エラー発生時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"エラーメッセージ: {error_msg}\n")
            if exception:
                f.write(f"例外タイプ: {type(exception).__name__}\n")
                f.write(f"例外メッセージ: {str(exception)}\n")
                f.write("\nトレースバック:\n")
                f.write(traceback.format_exc())
            f.write(f"\nPythonパス:\n")
            for path in sys.path:
                f.write(f"  {path}\n")
            f.write(f"\n作業ディレクトリ: {os.getcwd()}\n")
            if hasattr(sys, 'executable'):
                f.write(f"実行ファイル: {sys.executable}\n")
        
        print(f"エラーログを保存しました: {log_file}")
    except Exception as e:
        print(f"ログファイルの書き込みに失敗: {e}")

def main(page: ft.Page):
    page.title = "ミャクリャク"
    page.vertical_alignment = ft.MainAxisAlignment.START
    # OSのダークモード設定に関係なく、常にライトテーマで表示する
    page.theme_mode = ft.ThemeMode.LIGHT

    #初期化
    try:
        game_data = game_logic.initialize_game_data()
    except Exception as e:
        error_msg = f"ゲームデータの初期化中にエラーが発生しました: {e}"
        print(error_msg)
        traceback.print_exc()
        log_error(error_msg, e)
        page.add(ft.Text(
            f"ゲームの初期化に失敗しました。\nエラー: {str(e)}\n\nログファイルを確認してください。",
            color=ft.Colors.RED,
            size=14
        ))
        page.update()
        return
    
    if not game_data:
        error_msg = "ゲームデータが空です。モデルファイルを確認してください。"
        print(error_msg)
        log_error(error_msg)
        page.add(ft.Text(
            "ゲームの初期化に失敗しました。モデルファイルを確認してください。\n\nログファイルを確認してください。",
            color=ft.Colors.RED,
            size=14
        ))
        page.update()
        return

    target_word = game_data['target_word']
    rank_map = game_data['rank_map']

    answer_count = 0
    hint_count = 0
    guessed_words: Set[str] = set()
    game_clear = False

    #UI
    title_text = ft.Text(
        page.title,
        size = 36,
        weight = ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        expand=True
    )

    closest_words_dialog = ft.AlertDialog(
        modal=False, # モーダルではない
        title=ft.Text(target_word),
        content=ft.Container(height=300, content=ft.Column(scroll=ft.ScrollMode.ADAPTIVE), padding=0),
        actions=[
            # open を False にして閉じる（on_dismiss で overlay から削除）
            ft.TextButton("閉じる", on_click=lambda e: setattr(closest_words_dialog, "open", False) or page.update()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        # 閉じたら overlay から取り除き、残像を防ぐ
        on_dismiss=lambda e: page.overlay.remove(closest_words_dialog) or page.update(),
    )
    def show_closest_words(e):        
        MAX_RANK_TO_SHOW = 500
        
        revealed_words = {
            word: rank for word, rank in rank_map.items() 
            if rank <= MAX_RANK_TO_SHOW
        }
        
        # 順位でソート
        sorted_revealed = sorted(revealed_words.items(), key=lambda item: item[1])

        dialog_content_controls = []
        for word, rank in sorted_revealed:
            is_guessed = word in guessed_words
            if is_guessed:
                    bg_color = ft.Colors.GREEN_100 # 回答済みは薄い緑
            else:
                bg_color = ft.Colors.WHITE # 未回答は白

            dialog_content_controls.append(
                ft.Container(
                    ft.Row([
                        ft.Text(word, expand=True),
                        ft.Text(f"{rank}", width=40),
                    ], spacing=10),
                    padding=8,
                    margin=ft.margin.only(bottom=5),
                    bgcolor=bg_color,
                    border_radius=ft.border_radius.all(8),
                )
            )

        # ダイアログの内容を更新
        closest_words_dialog.content.content.controls = dialog_content_controls
        
        # ダイアログを表示（重複追加を防止）
        if closest_words_dialog not in page.overlay:
            page.overlay.append(closest_words_dialog)
        closest_words_dialog.open = True
        page.update()

    closest_words_button = ft.Container(
        content=ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.Icons.VISIBILITY, size=24),
                ft.Text("類似単語", size=18, weight=ft.FontWeight.W_600),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            on_click=show_closest_words,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=20)
            )
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=5, bottom=10),
        visible=False # 初期状態では非表示
    )

    def get_hint_rank(min_revealed_rank: Optional[int], initial_max_rank: int = 600) -> int:
        if min_revealed_rank is None or min_revealed_rank > 600:
            return initial_max_rank
        half_rank = math.ceil(min_revealed_rank / 2)
        base_rank = max(half_rank, 2) # 順位が1未満にならないように
        return min(initial_max_rank, base_rank)

    def find_unrevealed_word(target_rank: int) -> Optional[str]:
        rank = target_rank
        
        # rank_mapは {単語: 順位} のマップ
        # 順位でソートされた単語リストを生成
        sorted_words = sorted(rank_map.keys(), key=lambda w: rank_map[w])
        
        while rank <= len(sorted_words):
            word = sorted_words[rank - 1] # 順位は1ベース、リストインデックスは0ベース
            
            # 既に回答済み (normalized_input) のリストに含まれていないかチェック
            # ヒント単語も正規化してguessed_wordsに含まれているはずなので、
            # rank_mapのキー(単語)をそのままnormalized_inputとして使用できる
            if word not in guessed_words:
                return word
            
            # 既に明らかになっていたら、+1位を試す
            rank += 1
            
        return None # 適切なヒントが見つからなかった場合

    def close_dialog(e: ft.ControlEvent):
        nonlocal game_clear
        
        # ダイアログを閉じる
        confirm_give_up_dialog.open = False
        
        if e.control.data == 'yes':
            input_box.value = target_word  # 正解の単語を入力欄にセット
            add_item_to_list(e, is_hint=True)  # 引数を渡す
            # 「はい」が押されたときのギブアップ処理
            game_clear = True
            
            # スナックバーと状態メッセージの更新
            snack_bar = ft.SnackBar(ft.Text(f"🏳️ お手上げ！正解は '{target_word}' でした。"))
            page.overlay.append(snack_bar)
            snack_bar.open = True
            
            status_message.value = f"🏳️ お手上げしました。正解は '{target_word}' です。"
            status_hint_container.bgcolor = ft.Colors.AMBER_100
            status_hint_container.border = ft.border.all(2, ft.Colors.AMBER_700)
            closest_words_button.visible = True
        else:
            snack_bar = ft.SnackBar(ft.Text("ゲーム続行！"))
            page.overlay.append(snack_bar)
            snack_bar.open = True

        page.update()

    confirm_give_up_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("お手上げの確認"),
        content=ft.Text("本当にゲームを終了し、お手上げしてもよろしいですか？"),
        actions=[
            ft.TextButton("はい", on_click=close_dialog, data='yes', style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("いいえ", on_click=close_dialog, data='no'),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def handle_menu_click(e: ft.ControlEvent):
        nonlocal hint_count
        if game_clear:
            page.snack_bar = ft.SnackBar(ft.Text("✅ ゲームは既にクリアしています。"))
            page.snack_bar.open = True
            page.update()
            return         
        if e.control.data == "hint":
            min_rank = None
            # guessed_wordsに含まれる単語の順位を取得し、最小値を求める
            # target_wordはguessed_wordsに含まれるがrank_mapには含まれないため除外
            if guessed_words:
                revealed_ranks = [rank_map[w] for w in guessed_words if w in rank_map]
                if revealed_ranks:
                    min_rank = min(revealed_ranks)

            target_rank = get_hint_rank(min_rank)
            hint_word =find_unrevealed_word(target_rank)

            if hint_word:
                hint_count +=1
                hint_text.value = f"ヒント回数: {hint_count}"
                input_box.value = hint_word
                add_item_to_list(None, is_hint=True)
            else:
                snack_bar = ft.SnackBar(ft.Text("⚠️ これ以上、未回答の単語からヒントを提供できません。"))
                page.overlay.append(snack_bar)
        elif e.control.data == "give_up":
            # ギブアップ処理の例
            page.overlay.append(confirm_give_up_dialog)
            confirm_give_up_dialog.open = True
        page.update()

    menu_button = ft.PopupMenuButton(
        icon=ft.Icons.MENU,
        icon_size=30,
        tooltip="メニューを開く",
        items=[
            ft.PopupMenuItem(
                on_click=handle_menu_click,
                data="hint",
                content=ft.Container(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE),
                            ft.Text("ヒント", weight=ft.FontWeight.W_500),
                        ],
                    ),
                    padding=8,
                )
            ),
            ft.PopupMenuItem(
                on_click=handle_menu_click,
                data="give_up",
                content=ft.Container(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.FLAG),
                            ft.Text("お手上げ", weight=ft.FontWeight.W_500),
                        ],
                    ),
                    padding=8,
                )
            ),
        ]            
    )

    title_row = ft.Row(
        controls=[
            ft.Container(width=30), # 左側の余白（ハンバーガーボタンのサイズに合わせる）
            title_text,            # 中央に寄るタイトル
            menu_button,           # 右端のハンバーガーメニュー
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN, # 要素間のスペースを最大化
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    count_text = ft.Text(f"回答回数: {answer_count}")
    hint_text = ft.Text(f"ヒント回数: {hint_count}")
    
    count_row = ft.Row(
        controls=[
            count_text,
            hint_text,
        ]
    )

    last_input_text_content = ft.Row(
        controls=[
            ft.Text(
                value="",
                weight=ft.FontWeight.BOLD,
                expand=True,
            ),
            ft.Text(
                value="",
                weight=ft.FontWeight.BOLD,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    status_message = ft.Text(
        value=f"お題が選ばれました。（初期設定: {game_data['setup_time']:.2f} 秒）",
        color=ft.Colors.BLUE_GREY_900,
        weight=ft.FontWeight.W_500,
        size=16
    )
    status_hint_container = ft.Container(
        content=status_message,
        padding=10,
        margin=ft.margin.only(top=10, bottom=10),
        bgcolor=ft.Colors.CYAN_50,
        alignment=ft.alignment.center,
        border_radius=ft.border_radius.all(8),
        border=ft.border.all(2, ft.Colors.CYAN_700),
    )

    last_input_container = ft.Container(
        content=last_input_text_content,
        padding=8,
        margin=ft.margin.only(top=5, bottom=5),
        bgcolor=ft.Colors.YELLOW_100,
        alignment=ft.alignment.center_left,
        border_radius=ft.border_radius.all(8),
        border=ft.border.all(2),
        visible=False,
    )

    def update_status_visibility():
        status_hint_container.visible = status_message.value.strip() != ""

    def add_item_to_list(e, is_hint: bool = False):
        nonlocal answer_count
        nonlocal game_clear

        current_input = input_box.value.strip()

        if current_input:

            result = game_logic.check_guess(current_input, target_word, rank_map)
            normalized_input = result['normalized']

            if result['status'] == 'error':
                status_message.value = f"⚠️ 解析エラー: {result['message']}"
                status_hint_container.bgcolor = ft.Colors.RED_100
                status_hint_container.border = ft.border.all(2, ft.Colors.RED_700)
                update_status_visibility()
                page.update()
                return
            elif normalized_input in guessed_words:
                status_message.value = f"❌ 既に統一表記 '{normalized_input}' で回答済みです。"
                input_box.value = ""
                update_status_visibility()
                page.update()
                return

            guessed_words.add(normalized_input)

            if not is_hint and not game_clear:
                answer_count += 1

            count_text.value = f"回答回数: {answer_count}"
            hint_text.value = f"ヒント回数: {hint_count}"
            
            rank = result['rank']
        
            if result['status'] == 'correct':
                game_clear = True
                rank_display = "🎉 正解！"
                sort_rank = 1
                status_message.value = f"🎉🎉🎉 {normalized_input}！お題の単語です！"
                bg_color = ft.Colors.BLUE_100
                closest_words_button.visible = True
            elif result['status'] == 'incorrect_out_of_scope':
                rank_display = f"圏外 ({game_logic.TOP_N_CANDIDATES}+位)"
                sort_rank = game_logic.TOP_N_CANDIDATES + 2 # 圏外としてソート
                status_message.value = f"類似度が低すぎます。"            
                bg_color = ft.Colors.RED_100
            else:
                rank_display = f"{rank}"
                sort_rank = rank
                status_message.value = ""
                if rank <= 600:
                    bg_color = ft.Colors.BLUE_100
                elif rank <= 2000:
                    bg_color = ft.Colors.YELLOW_100
                else:
                    bg_color = ft.Colors.RED_100

            for old_item_container in lv.controls:
                # コンテナから枠線を削除
                old_item_container.border = None
                # コンテナ内のft.Textの太字を解除
                if isinstance(old_item_container.content, ft.Text):
                    old_item_container.content.weight = ft.FontWeight.NORMAL
            # 直前入力コンテナの更新
            last_input_text_content.controls[0].value = f"{normalized_input}"
            last_input_text_content.controls[1].value = f"{rank_display}"
            last_input_container.bgcolor = bg_color
            last_input_container.visible = True
            # 新しく追加するリスト項目に太字と枠線（強調スタイル）を設定する
            # ft.Textに太字設定
            new_item_content = ft.Row(
                controls=[
                    ft.Text(f"{normalized_input}", 
                            weight=ft.FontWeight.BOLD,
                            expand=True),
                    ft.Text(f"{rank_display}", weight=ft.FontWeight.BOLD),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
            # ft.Containerに枠線設定
            new_item = ft.Container(
                content=new_item_content,
                padding=8,
                margin=ft.margin.only(bottom=5),
                bgcolor=bg_color,
                alignment=ft.alignment.center_left,
                border_radius=ft.border_radius.all(8),
                border=ft.border.all(2),
            )
            new_item.rank = sort_rank

            lv.controls.append(new_item)

            lv.controls.sort(key=lambda item: item.rank)

            #input_boxの値をクリア
            input_box.value = ""
            update_status_visibility()
            page.update()

    input_box = ft.TextField(
        label="単語を入力してください",
        suffix=ft.IconButton(
            icon = ft.Icons.SEND,
            tooltip="送信",
            on_click=lambda e: add_item_to_list(e, is_hint=False),
        ),
        on_submit=lambda e: add_item_to_list(e, is_hint=False),
    )

    lv = ft.ListView(
        controls=[],
        expand=True,
    )

    page.add(
        title_row,
        closest_words_button,
        count_row,
        status_hint_container,
        input_box,
        last_input_container,
        lv,
    )

if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        error_msg = f"アプリの起動中にエラーが発生しました: {e}"
        print(error_msg)
        traceback.print_exc()
        log_error(error_msg, e)
        # コンソールがすぐに閉じないようにする
        input("\nエラーが発生しました。Enterキーを押して終了してください...")
        sys.exit(1)
