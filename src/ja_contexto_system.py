"""
Web（Pyodide）環境では `gensim` と `sudachipy` が利用できないため、
インポートに失敗した場合は軽量スタブに自動フォールバックする。
ローカル/デスクトップ環境では従来通り本物のライブラリを使用する。
"""

try:
    import gensim  # type: ignore
    HAS_GENSIM = True
except Exception:
    gensim = None  # type: ignore
    HAS_GENSIM = False

try:
    from sudachipy import tokenizer, dictionary  # type: ignore
    HAS_SUDACHI = True
except Exception:
    tokenizer = None  # type: ignore
    dictionary = None  # type: ignore
    HAS_SUDACHI = False
import random
import sys
try:
    import numpy as np  # type: ignore
    HAS_NUMPY = True
except Exception:
    np = None  # type: ignore
    HAS_NUMPY = False
import time 
from typing import List, Tuple, Dict, Set, Optional
import os

# --- 定数設定 ---
TOP_N_CANDIDATES = 50000  # 順位計算の対象とする類似語の数
# **修正:** PyInstaller環境でのパス解決を確実に行う
if getattr(sys, 'frozen', False):
    # PyInstaller環境: モデルは実行ファイルと同じディレクトリにある
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 開発環境: スクリプトのディレクトリを基準とする
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR, 
    'chive-1.3-mc90_gensim', 
    'chive-1.3-mc90.kv'
)# ユーザー指定の出題リスト
FIXED_WORD_LIST = ['犬', '猫', '鳥', '魚', '象', '馬', '牛', '豚', '羊', '猿', '兎', 
                    '鼠', '蛙', '蛇', '蜘蛛', '蟻', '蝶', '蜂', '蟹', '海老', '花', '木', 
                    '草', '葉', '林檎', '種', '森', '山', '川', '海', '空', '雲', '雨', 
                    '雪', '風', '太陽', '水', '星', '家', '部屋', '窓', '壁', '床', 
                    '机', '椅子', '本', '鉛筆', '消しゴム', 'ノート', '筆箱', '時計', '鏡', 
                    '電気', '電話', '皿', 'コップ', '箸', '靴', '服', '帽子', '手袋', '傘', 
                    '鞄', '財布', '鍵', '車', '電車', '船', '飛行機', '自転車', '道', '橋', 
                    '駅', '学校', '公園', '病院', '店', '銀行', '石', '砂', '泥', 
                    '氷', '火', '光', '音', '声', '匂い', '味', '青', '数', 'カラオケ', 
                    'お母さん', 'カレンダー', 'お茶', '年', '朝', '昼', '夜', '春', '夏', '秋', '冬', 
                    'そろばん', '将棋', '上', '下', 'ホワイトボード', '机', '神社', 'ハンドル', 
                    '顔', '目', '耳', '鼻', '口', '手', '足', '指', '髪', '肌', '血', 
                    '骨', '夢', 'メール', '歌', '絵', '遊具', '仕事', '飯', '牛乳', '卵', '肉', 
                    '魚', '野菜', '果物', '米', '塩', '砂糖', '醤油', '味噌', '油', '茶', '氷', 
                    '友達', '家族', '先生', '注射', '警察', '消防車', 'タクシー', 'オムライス', 
                    '口紅', '客', '子供', '大人', '男', '女', '命', '勇気', 'お土産', '力', '手紙', 
                    '写真', '新聞', '漫画', '音楽', '映画', '人形', '風船', 'ボール', '縄', 
                    '箱', '袋', '紙', '布', '糸', '針', '釘', '電池', '薬', '博士', 
                    '怪我', '汗', '涙', '笑顔', '聞く', '答え', '秘密', '約束', '実験', 
                    '宝', 'お金', '休み', '布団', '会話', '話', '読む', '趣味', 'お見合い', 
                    '運動会', '鉄棒', '指輪', '宝石', '粘土', '滑り台', '絵本', '図鑑', '地図', 
                    '旗', '祭', '誕生日', '冒険', '唐揚げ', '魔法', '姫', '王様', 'お化け', '鬼', '泥棒', 
                    '化粧', '香水', '池', '噴水', '看板', '信号', '横断歩道', '尻尾', '髭', '爪', 
                    '羽', '虫', '食物', '洋服', 'お守り', 'ろうそく', '靴下', '石鹸', '歯磨き', '風呂', 
                    'トイレ', 'ティッシュ', '紐', '菓子', '焼き鳥', 'うどん', '水筒', '遠足', '庭', '団子', 
                    '飴', '玉子焼き', '味噌汁', '弁当', '遊園地', '動物園', '水族館', '博物館', '美術館', 
                    '体育館', '図書館', 'ロケット', 'ロボット', '恐竜', 'パズル', '積み木', '砂場', 'ブランコ', 
                    'シーソー', '絵筆', 'クレヨン', 'ハサミ', '糊', 'テープ', 'ビー玉', '独楽', 'かるた', 'すごろく', 
                    '地面', 'ポスト', 'ごみ箱', '水道', '玄関', '廊下', '階段', '屋上', '地下', 
                    'マフラー', '柵', '手すり', '壁', '電球', 'コンセント', 'ボタン', 'キーホルダー', 
                    'バケツ', '雑巾', '箒', 'ちりとり', '上履き', 'スリッパ', '絨毯', 'カーテン', '枕',  
                    '洗濯機', 'おもちゃ', '塗り絵', '色鉛筆', '手帳', 'カバン', 'スカーフ', 'スカート', 
                    'ズボン', 'シャツ', 'セーター', 'ジャケット', '手袋', 'ハンカチ', 'ティッシュ', 'タオル', 
                    '歯ブラシ', 'シャンプー', '鏡', '棚', '長靴']

# --- 1. Sudachiの初期化 ---
if HAS_SUDACHI:
    tokenizer_obj = None
    mode = None
    try:
        # まずは標準的な方法で初期化を試みる
        tokenizer_obj = dictionary.Dictionary().create()
        mode = tokenizer.Tokenizer.SplitMode.C
        print("✅ Sudachiの初期化に成功しました。")
    except Exception as inner_e:
        # 辞書が見つからない場合の詳細なエラー情報
        print(f"⚠️ Sudachi辞書の初期化に失敗 (最初の試行): {inner_e}")
        print(f"   実行ファイルパス: {sys.executable if hasattr(sys, 'executable') else 'N/A'}")
        print(f"   作業ディレクトリ: {os.getcwd()}")
        print(f"   Pythonパス (最初の5つ): {sys.path[:5]}")
        
        # pkg_resourcesを使って辞書パスを探す
        try:
            import pkg_resources
            sudachidict_path = pkg_resources.resource_filename('sudachidict_core', '')
            print(f"   sudachidict_coreパッケージパス (pkg_resources): {sudachidict_path}")
            
            if os.path.exists(sudachidict_path):
                print(f"   ✅ 辞書パスは存在します: {sudachidict_path}")
                # 環境変数を設定して再試行
                os.environ['SUDACHI_RESOURCE_ROOT'] = sudachidict_path
                print(f"   環境変数 SUDACHI_RESOURCE_ROOT を設定: {sudachidict_path}")
                
                # 再度初期化を試みる
                tokenizer_obj = dictionary.Dictionary().create()
                mode = tokenizer.Tokenizer.SplitMode.C
                print("✅ Sudachiの初期化に成功しました（環境変数設定後）。")
            else:
                print(f"   ❌ 辞書パスが存在しません: {sudachidict_path}")
                # sys.pathから探す
                for path in sys.path:
                    potential_dict_path = os.path.join(path, 'sudachidict_core')
                    if os.path.exists(potential_dict_path):
                        print(f"   ✅ 代替パスを発見: {potential_dict_path}")
                        os.environ['SUDACHI_RESOURCE_ROOT'] = potential_dict_path
                        tokenizer_obj = dictionary.Dictionary().create()
                        mode = tokenizer.Tokenizer.SplitMode.C
                        print("✅ Sudachiの初期化に成功しました（代替パス使用）。")
                        break
                else:
                    print(f"   ❌ 辞書パスが見つかりませんでした。")
                    raise inner_e  # 元のエラーを再発生
        except Exception as pkg_e:
            print(f"   ⚠️ パッケージパスの解決に失敗: {pkg_e}")
            import traceback
            traceback.print_exc()
            # 最終的に失敗した場合
            tokenizer_obj = None
            mode = None
            HAS_SUDACHI = False
    except Exception as e:
        print(f"❌ エラー: Sudachiの初期化に完全に失敗しました。")
        print(f"   エラー詳細: {e}")
        import traceback
        traceback.print_exc()
        print(f"   ⚠️ 正規化機能が無効になります。入力されたテキストはそのまま使用されます。")
        tokenizer_obj = None
        mode = None
        HAS_SUDACHI = False
else:
    tokenizer_obj = None
    mode = None
    print("⚠️ sudachipyがインポートできません。正規化機能が無効になります。")


# --- 2. Word2Vecモデルのロードとダミーモデルの準備 ---
class SimpleKeyedVectors:
    """gensim.models.KeyedVectors の極小互換クラス（Web フォールバック用）。"""
    def __init__(self, vector_size: int):
        self.vector_size = vector_size
        self._key_to_vec: Dict[str, List[float]] = {}
        self.index_to_key: List[str] = []

    def add_vector(self, key: str, vector: List[float]) -> None:
        if key not in self._key_to_vec:
            self.index_to_key.append(key)
        self._key_to_vec[key] = vector

    def most_similar(self, key: str, topn: int = 10):
        # ダミーモデルでは固定の擬似スコアを返す（下の DUMMY_TOP_LIST_DOG を使用）
        return []

try:
    print(f"モデル '{MODEL_PATH}' をロード中...")
    if HAS_GENSIM:
        model = gensim.models.KeyedVectors.load(MODEL_PATH)  # type: ignore[attr-defined]
        MODEL_LOADED = True
        print("モデルロード完了。")
    else:
        raise FileNotFoundError("gensim 不在のためロード不可（Web フォールバックへ）")
except Exception:
    print(f"⚠️ 警告: モデルファイルが見つかりません ('{MODEL_PATH}')。ダミーモデルを使用します。")
    MODEL_LOADED = False
    
    # ダミーモデルの作成 (ゲーム実行に必要な最低限の語彙とリスト)
    ALL_VOCAB = FIXED_WORD_LIST + ['トマト', 'ミカン', 'バナナ', 'キャベツ', 'キュウリ', 'ナス', '💧', '走る', '美しい', 'じゃがいも', 'ジャガ芋']
    # 実モデルが 365 次元なのでダミーも同次元に合わせる
    model = SimpleKeyedVectors(vector_size=365) if not HAS_GENSIM else gensim.models.KeyedVectors(vector_size=365)  # type: ignore[attr-defined]

    def _rand_vec(n: int) -> List[float]:
        if HAS_NUMPY:
            return [float(x) for x in np.random.rand(n)]  # type: ignore[attr-defined]
        import random as _random
        return [_random.random() for _ in range(n)]

    for i, word in enumerate(ALL_VOCAB):
        model.add_vector(word, _rand_vec(365))
    
    # '犬'がお題の場合のダミー類似度リストを固定で作成 (絵文字の'💧'と動詞の'走る'を含む)
    DUMMY_TOP_LIST_DOG = [
        ('猫', 0.95), ('走る', 0.88), ('トマト', 0.85), 
        ('美しい', 0.80), # 形容詞
        ('💧', 0.60), 
        ('バナナ', 0.50), ('キャベツ', 0.45), 
    ]
    
    # get_normalized_token()のテスト用ダミー
    DUMMY_NORM_MAP = {'じゃがいも': 'ジャガ芋', 'ジャガイモ': 'ジャガ芋', '犬': '犬'}
    
    def dummy_most_similar(key, topn=10):
        if key in [get_normalized_token(w) for w in FIXED_WORD_LIST]:
            return DUMMY_TOP_LIST_DOG
        return []
        
    model.most_similar = dummy_most_similar


# --- 3. ヘルパー関数 ---

def get_normalized_token(text: str) -> Optional[str]:
    """ Sudachiで解析し、モデルの語彙に合う可能性の高い標準形を返します。
        解析不能な場合は None を返します。
    """
    if not MODEL_LOADED and text in DUMMY_NORM_MAP:
        # ダミーモードでの正規化テスト用
        return DUMMY_NORM_MAP.get(text)
        
    if HAS_SUDACHI and tokenizer_obj is not None and mode is not None:
        tokens = tokenizer_obj.tokenize(text, mode)
        return tokens[0].normalized_form() if tokens else None
    # フォールバック: そのまま返す（テスト用にダミー正規化マップを優先）
    return text

def is_proper_noun(word: str) -> bool:
    """ Sudachiの品詞情報に基づき、単語が固有名詞であるかを判定します。 """
    if HAS_SUDACHI and tokenizer_obj is not None and mode is not None:
        tokens = tokenizer_obj.tokenize(word, mode)
        if not tokens: return False
        pos = tokens[0].part_of_speech()
        return len(pos) > 1 and pos[0] == '名詞' and pos[1] == '固有名詞'
    # フォールバック: 判定不能なので False（=除外しない）
    return False

def has_emoji(text: str) -> bool:
    """ テキスト内に絵文字が含まれているかを判定します。 """
    for char in text:
        if 0x2600 <= ord(char) <= 0x27BF:
            return True
        if 0x1F300 <= ord(char) <= 0x1FAFF:
            return True
    return False

# --- 4. ゲームの初期化 ---

# ゲームの状態を保持するためのクラスや辞書は使用せず、
# UI側が必要なデータを取得できる関数を定義します。

def initialize_game_data() -> Dict[str, any]:
    """ ゲームの初期化を行い、お題と順位付けに必要なデータを返します。
        エラー時は空の辞書を返すか、例外を投げます。
    """
    try:
        start_time = time.time()
        # お題と順位付けの元になるリストを生成
        target_word_norm, top_rank_list = select_target_word_and_list(model)
    except Exception as e:
        print(f"ゲームの初期化に失敗しました: {e}", file=sys.stderr)
        return {}

    rank_map = {word: rank + 1 for rank, (word, score) in enumerate(top_rank_list)}
    
    end_time = time.time()
    setup_time = end_time - start_time
    
    return {
        'target_word': target_word_norm,
        'rank_map': rank_map,
        'top_rank_list': top_rank_list, # 終了時の開示用
        'setup_time': setup_time,
    }

def select_target_word_and_list(model) -> Tuple[str, List[Tuple[str, float]]]:
    """ 固定リストからお題を選択し、その単語に対する類似度トップリストを作成します。 """
    
    target_word_surface = random.choice(FIXED_WORD_LIST)
    target_word = get_normalized_token(target_word_surface)
    
    if target_word is None or target_word not in model.index_to_key:
         raise ValueError(f"お題候補 '{target_word_surface}' ({target_word}) はモデルの語彙にありません。")


    # 類似語リストの生成
    raw_top_list = model.most_similar(target_word, topn=TOP_N_CANDIDATES * 2)
    
    # トップリストからお題自体、固有名詞、絵文字を除外
    filtered_list = []
    for word, score in raw_top_list:
        if word == target_word:
            continue
        if is_proper_noun(word) or has_emoji(word):
            continue
            
        filtered_list.append((word, score))
    
    top_rank_list = filtered_list[:TOP_N_CANDIDATES]
        
    # 0位（お題単語）をリストの先頭に追加
    top_rank_list.insert(0, (target_word, 1.0))
    
    return target_word, top_rank_list

def check_guess(user_input: str, target_word: str, rank_map: Dict[str, int]) -> Dict[str, any]:
    """ ユーザーの入力単語をチェックし、結果（正規化単語、順位、正解/不正解）を返します。
    """
    normalized_input = get_normalized_token(user_input)
    
    if normalized_input is None:
        return {'status': 'error', 'message': f"'{user_input}' は解析できませんでした。", 'normalized': None}
    
    if normalized_input == target_word:
        return {'status': 'correct', 'message': "🎉🎉🎉 正解です！", 'normalized': normalized_input, 'rank': 0}
    
    rank = rank_map.get(normalized_input)
    
    if rank is None:
        return {
            'status': 'incorrect_out_of_scope', 
            'message': f"❌ 類似度が低すぎ、トップリスト圏外です。", 
            'normalized': normalized_input, 
            'rank': TOP_N_CANDIDATES + 1
        }
    else:
        return {
            'status': 'incorrect', 
            'message': f"❌ 不正解。", 
            'normalized': normalized_input, 
            'rank': rank
        }

# --- 5. メインゲームループ ---

def start_game():
    
    try:
        # お題と順位付けの元になるリストを生成
        data = initialize_game_data()
    except Exception as e:
        print(f"ゲームの初期化に失敗しました: {e}")
        print("終了します。")
        return
        
    target_word = data['target_word']
    rank_map = data['rank_map']
    top_rank_list = data['top_rank_list']
    setup_time = data['setup_time']
        
    guessed_words: Set[str] = set()

    print("-" * 50)
    print("      単語当て類似度ゲームを開始します      ")
    print(f"  （初期設定時間: {setup_time:.2f} 秒）")
    print("-" * 50)
    print(f"✅ お題の単語がリストからランダムに選ばれました。")
    print(f"👉 類似度順位は最大 **{TOP_N_CANDIDATES} 位** まで出ます。\n")
    print("単語を入力してください ('q'で終了)。品詞の制限はありません。")
    print("----------------------------------------")
    
    attempt = 0
    while True:
        
        # ユーザー入力
        try:
            user_input = input(f"【第 {attempt + 1} 回】単語を入力: ").strip()
        except EOFError:
            print("\nゲームを終了します。")
            break
        except KeyboardInterrupt:
            print("\nゲームを中断します。")
            break

        if user_input.lower() in ('q', 'exit'):
            print("\nゲームを終了します。")
            break
            
        if not user_input:
            continue

        result = check_guess(user_input, target_word, rank_map)
        normalized_input = result.get('normalized')
        
        # --- 正規化結果の表示 (NEW) ---
        print(f"   ➡️ 統一表記: '{normalized_input}'")
        # -------------------------------
            
        # 3. 入力チェック (重複判定)
        if normalized_input in guessed_words:
            print(f"❌ 既に統一表記 '{normalized_input}' で入力されています。別の単語を入力してください。")
            continue
            
        guessed_words.add(normalized_input)
        attempt += 1

        # 4. 正解判定
        if result['status'] == 'correct':
            print("\n🎉🎉🎉 正解です！おめでとうございます！ 🎉🎉🎉")
            break
        
        # 5. 類似度順位の計算とヒントの提示
        rank = rank_map.get(normalized_input)

        if rank is None:
            print(f"❌ 残念、'{user_input}' は不正解です。")
            print(f"👉 ヒント: 類似度が低すぎ、トップリスト圏外です。（{TOP_N_CANDIDATES + 1}位以下相当）")
        else:
            print(f"❌ 残念、'{user_input}' は不正解です。")
            print(f"👉 ヒント: お題の単語との類似度順位は **{rank} 位** です！")
            
            # 追加のヒント
            if rank <= 5:
                print("🔥 激アツ！非常に近い単語です！")
            elif rank <= 50:
                print("🌟 類似度が高めです。意味のカテゴリーが近いかもしれません。")
            elif rank <= 500:
                print("💡 そこそこ近いです。頑張ってください！")
            elif rank <= 5000:
                print("🔍 かなり広範囲ですが、ヒントは出ています。")
                
        print("-" * 30)

    # 6. ゲーム終了時の答えとトップ50の開示
    print("\n--- ゲーム終了 ---")
    print(f"正解は **'{target_word}'** でした！ (全 {attempt} 回で終了)")
    
    # トップ50リストを取得 (top_rank_listの先頭51要素、0位はお題単語)
    top_50_list = top_rank_list[:51]
    
    print("\n✨ 類似度トップ50リスト (固有名詞・絵文字なし):")
    for i, (word, score) in enumerate(top_50_list):
        if i == 0:
            print(f"  {i+1:>6}位 (お題): {word}")
        else:
            print(f"  {i+1:>6}位: {word} (類似度: {score:.4f})")
            
    print("-" * 50)
    
# --- ゲーム開始 ---
if __name__ == "__main__":
    start_game()