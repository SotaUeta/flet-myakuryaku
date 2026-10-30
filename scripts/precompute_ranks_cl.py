"""
お題候補（FIXED_WORD_LIST）ごとに類似度順位を事前計算し、src/rank_data/ に保存する。

モデル (src/chive-1.3-mc90_gensim/) と Sudachi が使える環境で、リポジトリのルートから実行する:
    python scripts/precompute_ranks_cl.py

出力:
    src/rank_data/index.json   お題と順位ファイルの対応表
    src/rank_data/NNN.txt.gz   1行1語、順位順（1行目はお題）

FIXED_WORD_LIST・TOP_N_CANDIDATES・除外条件を変えたときは再実行すること。
"""
import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import ja_contexto_system as game_logic


def main():
    model = game_logic.load_model()
    if not game_logic.MODEL_LOADED:
        sys.exit(f"モデルをロードできませんでした: {game_logic.MODEL_PATH}")
    if not game_logic.HAS_SUDACHI:
        sys.exit("Sudachi が使えないため、正規化と固有名詞の除外ができません。")

    out_dir = game_logic.RANK_DATA_DIR
    os.makedirs(out_dir, exist_ok=True)
    # 古いデータが残らないよう、このスクリプトが作るファイルだけを消す
    for name in os.listdir(out_dir):
        if name.endswith('.txt.gz') or name == 'index.json':
            os.remove(os.path.join(out_dir, name))

    targets = []
    skipped = []
    start_time = time.time()
    for surface in game_logic.FIXED_WORD_LIST:
        target_word = game_logic.get_normalized_token(surface)
        if any(t['word'] == target_word for t in targets):
            continue  # 重複（正規化後に同じになるものを含む）
        try:
            target_word, top_rank_list = game_logic.build_rank_list(model, surface)
        except ValueError as e:
            print(f"スキップ: {e}")
            skipped.append(surface)
            continue

        file_name = f"{len(targets):03d}.txt.gz"
        with gzip.open(os.path.join(out_dir, file_name), 'wt', encoding='utf-8') as f:
            f.write('\n'.join(word for word, _ in top_rank_list))
        targets.append({'word': target_word, 'file': file_name})
        print(f"[{len(targets)}] {target_word} ({time.time() - start_time:.0f} 秒経過)")

    # 途中で止まっても中途半端な目次が残らないよう、目次は最後に書く
    with open(game_logic.RANK_INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump({'top_n': game_logic.TOP_N_CANDIDATES, 'targets': targets}, f, ensure_ascii=False, indent=1)

    print(f"\n完了: {len(targets)} 語を保存しました（{time.time() - start_time:.0f} 秒）。")
    if skipped:
        print(f"語彙に無いためスキップ: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
