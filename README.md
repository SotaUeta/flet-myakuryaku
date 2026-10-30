# Flet app

A simple Flet app.

To run the app:

```
flet run [app_directory]
```

chive-1.3-mc90_gensim をダウンロードして src/ 以下に配置してください
## 類似度順位の事前計算

お題ごとの類似度順位を事前に計算しておくと、ゲーム開始時の待ち時間がほぼなくなります（モデルも読み込まなくなります）。
モデルを `src/` に配置したうえで、リポジトリのルートで一度だけ実行してください。

```
python scripts/precompute_ranks_cl.py
```

結果は `src/rank_data/` に保存されます。お題リスト（`FIXED_WORD_LIST`）や `TOP_N_CANDIDATES` を変えたときは再実行してください。
`src/rank_data/` が無い場合は、従来どおりゲームごとにモデルから計算します。
