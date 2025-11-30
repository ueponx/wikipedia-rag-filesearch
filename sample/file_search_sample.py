import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .envファイルから環境変数を読み込む
load_dotenv()

# クライアントの作成
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")
store_name = os.getenv("STORE_NAME")  # 既存のStore名（あれば）

# 既存Storeを使用するか、新規作成するか
if store_name:
    print(f"Using existing store: {store_name}")
    # 既存Storeを使用（Store objectを取得）
    # Note: 既存Store名を使ってそのまま利用
    class ExistingStore:
        def __init__(self, name):
            self.name = name
    
    store = ExistingStore(store_name)
else:
    # 新しいStoreを作成
    print("Creating new file search store...")
    store = client.file_search_stores.create(
        config={'display_name': 'wikipedia-knowledge-base'}
    )
    print(f"Store created: {store.name}")
    print("\n" + "="*70)
    print("💡 To reuse this store and save costs, add this to your .env file:")
    print(f"STORE_NAME={store.name}")
    print("="*70 + "\n")

# sample.mdをアップロード
file_path = "sample.md"

if os.path.exists(file_path):
    print(f"\nUploading {file_path}...")
    
    # ファイルをアップロード
    operation = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=store.name,
        file=file_path
    )
    
    # 完了待機
    while not operation.done:
        print("Waiting for upload to complete...")
        time.sleep(1)
        operation = client.operations.get(operation)
    
    print("Upload completed successfully!")
else:
    print(f"Error: {file_path} not found in current directory")
    exit(1)

# File Searchを使った質問応答
print("\n" + "="*50)
print("File Search Question Answering Demo")
print("="*50)

query = "作家がAnthropicを提訴した訴訟の判決内容を教えてください"
print(f"\nQuestion: {query}")
print("\nGenerating answer...")

response = client.models.generate_content(
    model=model_name,
    contents=query,
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[store.name]
                )
            )
        ],
        temperature=0.7
    )
)

print(f"\nAnswer:\n{response.text}")
