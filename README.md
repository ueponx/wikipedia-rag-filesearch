# Wikipedia RAG File Search システム

Gemini File Search APIを使用したWikipedia記事検索RAGシステムです。

## 特徴

- ✅ **簡単セットアップ**: ベクトルDBの管理不要
- ✅ **自動引用機能**: 回答の根拠を自動表示
- ✅ **日本語対応**: 日本語ファイル名を自動変換
- ✅ **コスト最適化**: Storeの再利用でコスト削減

## 必要要件

- Python 3.8以上
- Google Gemini API キー

## セットアップ

### 1. プロジェクトのクローン

```bash
git clone https://github.com/ueponx/wikipedia-rag-filesearch.git
cd wikipedia-rag-filesearch
```

### 2. 仮想環境の作成（uvを使用）

```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトのセットアップ
uv venv
source .venv/bin/activate  # WSL/Linux/Mac
# または .venv\Scripts\activate  # Windows

# 依存パッケージのインストール
uv pip install google-genai python-dotenv tqdm
```

### 3. 環境変数の設定

```bash
# .envファイルを作成
cp .env.sample .env

# .envファイルを編集してAPIキーを設定
# GOOGLE_API_KEY=your_api_key_here
```

APIキーは[Google AI Studio](https://aistudio.google.com/app/apikey)で取得できます。

### 4. Wikipediaデータの準備

`data/wikipedia/`ディレクトリにWikipedia記事のmarkdownファイルを配置します。

```bash
mkdir -p data/wikipedia
# Wikipediaデータをコピー
cp /path/to/your/wikipedia/*.md data/wikipedia/
```

## 使用方法

### 1. データのアップロード

初回実行時は以下を実行してFile Search Storeを作成し、データをアップロードします：

```bash
python data_loader_filesearch.py
```

実行後、コンソールに表示される`STORE_NAME`を`.env`ファイルに追加してください：

```
STORE_NAME=fileSearchStores/wikipediaknowledgebase-abc123
```

### 2. テスト・質問応答

```bash
python test_rag_filesearch.py
```

以下のメニューが表示されます：

1. **質問応答テスト** - 単発の質問に回答
2. **インタラクティブモード** - 連続して質問可能
3. **統計情報の表示** - Store内のファイル数などを確認
4. **ファイルマッピング一覧** - アップロードしたファイルの一覧
5. **終了**

## ファイル構成

```
wikipedia-rag-filesearch/
├── .env                        # 環境変数（APIキー等）
├── .env.sample                 # 環境変数のサンプル
├── rag_system_filesearch.py    # RAGシステム本体
├── data_loader_filesearch.py   # データアップローダー
├── test_rag_filesearch.py      # テスト・デモ
├── file_mappings.json          # ファイル名マッピング（自動生成）
├── data/
│   └── wikipedia/              # Wikipediaデータ
└── README.md                   # このファイル
```

## コマンドオプション

### data_loader_filesearch.py

```bash
# 基本的な使い方
python data_loader_filesearch.py

# データディレクトリを指定
python data_loader_filesearch.py --data-dir ./my_data

# 既存データをリセットして再アップロード
python data_loader_filesearch.py --reset

# ヘルプを表示
python data_loader_filesearch.py --help
```

## プログラムから使用する

```python
from rag_system_filesearch import WikipediaRAGFileSearch

# RAGシステムの初期化
rag = WikipediaRAGFileSearch()

# 質問応答
answer = rag.generate_answer("機械学習について教えてください")
print(answer)

# Store情報の取得
store_info = rag.get_store_info()
print(f"Store名: {store_info['store_name']}")

# ファイル一覧の取得
files = rag.list_files_in_store()
print(f"総ファイル数: {len(files)}件")
```

## トラブルシューティング

### STORE_NAMEが設定されていないエラー

```
警告: STORE_NAMEが設定されていません。
```

**解決方法**: `data_loader_filesearch.py`を実行し、表示される`STORE_NAME`を`.env`に追加してください。

### 日本語ファイル名のエラー

File Search APIは日本語ファイル名を直接受け付けません。本システムでは自動的にASCII名に変換しますが、元のファイル名との対応は`file_mappings.json`で管理されます。

### アップロードタイムアウト

大きなファイルのアップロードに失敗する場合、`data_loader_filesearch.py`の`timeout`値を増やしてください（デフォルト: 60秒）。

## 料金について

File Search APIはインデックス作成時に課金されます。コストを削減するため：

- `.env`に`STORE_NAME`を設定して既存Storeを再利用
- 不要なファイルは削除
- `--reset`オプションは慎重に使用

詳細は[公式ドキュメント](https://ai.google.dev/gemini-api/docs/file-search?hl=ja)を参照してください。

## 参考リンク

- [Gemini File Search 公式ブログ](https://blog.google/technology/developers/file-search-gemini-api/)
- [File Search API ドキュメント](https://ai.google.dev/gemini-api/docs/file-search?hl=ja)
- [従来版RAGシステム](https://github.com/ueponx/wikipedia-rag-system)

## ライセンス

MIT License

## 作者

ueponx
