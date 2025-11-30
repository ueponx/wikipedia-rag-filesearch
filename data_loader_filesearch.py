import os
import json
import time
import hashlib
import argparse
from pathlib import Path
from tqdm import tqdm
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def safe_filename(original_filename):
    """日本語ファイル名を安全なASCII名に変換
    
    Args:
        original_filename: 元のファイル名
        
    Returns:
        安全なASCII名のファイル名
    """
    name, ext = os.path.splitext(original_filename)
    # ファイル名のハッシュ値を使用
    hash_name = hashlib.md5(name.encode('utf-8')).hexdigest()[:16]
    return f"wiki_{hash_name}{ext}"


def load_file_mappings(mapping_file='file_mappings.json'):
    """ファイルマッピングを読み込み
    
    Args:
        mapping_file: マッピングファイルのパス
        
    Returns:
        マッピング辞書
    """
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_file_mappings(mappings, mapping_file='file_mappings.json'):
    """ファイルマッピングを保存
    
    Args:
        mappings: マッピング辞書
        mapping_file: マッピングファイルのパス
    """
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)


def get_or_create_store(client, store_name=None):
    """File Search Storeを取得または作成
    
    Args:
        client: Gemini APIクライアント
        store_name: 既存のStore名（Noneの場合は新規作成）
        
    Returns:
        Store object
    """
    if store_name:
        print(f"既存のStoreを使用: {store_name}")
        # 既存Storeを使用
        class ExistingStore:
            def __init__(self, name):
                self.name = name
        return ExistingStore(store_name)
    else:
        # 新しいStoreを作成
        print("新しいFile Search Storeを作成中...")
        store = client.file_search_stores.create(
            config={'display_name': 'wikipedia-knowledge-base'}
        )
        print(f"Store作成完了: {store.name}")
        print("\n" + "=" * 70)
        print("💡 コスト削減のため、.envファイルに以下を追加してください:")
        print(f"STORE_NAME={store.name}")
        print("=" * 70 + "\n")
        return store


def delete_store_files(client, store_name, mapping_file='file_mappings.json'):
    """Store内のファイル情報をリセット
    
    Note: File Search APIではStore内の個別ファイル削除が困難なため、
    マッピング情報のみをクリアします。Store自体を削除する場合は、
    .envのSTORE_NAMEを削除して新規作成してください。
    
    Args:
        client: Gemini APIクライアント
        store_name: Store名
        mapping_file: マッピングファイルのパス
    """
    try:
        print("ファイルマッピング情報をクリア中...")
        
        # マッピング情報をクリア
        if os.path.exists(mapping_file):
            os.remove(mapping_file)
            print(f"{mapping_file}を削除しました")
        
        print("\n⚠️ 注意: Store内のファイルは削除されていません")
        print("完全にリセットする場合は、以下の手順を実行してください:")
        print("1. .envファイルのSTORE_NAMEを削除または空にする")
        print("2. data_loader_filesearch.pyを再実行（新しいStoreが作成されます）")
        print(f"\n現在のStore名: {store_name}")
        
    except Exception as e:
        print(f"リセット中にエラー: {e}")


def upload_wikipedia_data(data_dir, reset=False, mapping_file='file_mappings.json'):
    """WikipediaデータをFile Search Storeにアップロード
    
    Args:
        data_dir: データディレクトリ
        reset: 既存データをリセットするか
        mapping_file: マッピングファイルのパス
    """
    # クライアントの作成
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    store_name = os.getenv("STORE_NAME")
    
    # Storeの取得または作成
    if reset and store_name:
        confirm = input("既存のStoreをリセットしますか？ (y/N): ")
        if confirm.lower() == 'y':
            # マッピング情報をクリア
            delete_store_files(client, store_name, mapping_file)
            print("データをリセットしました\n")
    
    store = get_or_create_store(client, store_name)
    
    # データディレクトリの存在確認
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"エラー: ディレクトリ '{data_dir}' が見つかりません")
        return
    
    # markdownファイルの読み込み
    md_files = list(data_path.glob("*.md"))
    
    if not md_files:
        print(f"{data_dir} にmarkdownファイルが見つかりません")
        return
    
    print(f"{len(md_files)}件のファイルをアップロードします...\n")
    
    # ファイルマッピングの読み込み
    mappings = load_file_mappings(mapping_file)
    
    # 各ファイルの処理
    success_count = 0
    error_count = 0
    
    for file_path in tqdm(md_files, desc="データアップロード中"):
        try:
            original_name = file_path.name
            ascii_name = safe_filename(original_name)
            
            # 一時ファイルとして保存（ASCII名）
            temp_path = file_path.parent / ascii_name
            
            # ファイルをコピー（ASCII名で）
            import shutil
            shutil.copy2(file_path, temp_path)
            
            try:
                tqdm.write(f"アップロード中: {original_name} -> {ascii_name}")
                
                # ファイルをアップロード
                operation = client.file_search_stores.upload_to_file_search_store(
                    file_search_store_name=store.name,
                    file=str(temp_path),
                    config={
                        'display_name': file_path.stem,
                    }
                )
                
                # 完了待機（公式推奨: 5秒間隔、タイムアウト: 120秒）
                timeout = 120
                start_time = time.time()
                while not operation.done:
                    if time.time() - start_time > timeout:
                        raise TimeoutError("アップロードがタイムアウトしました")
                    time.sleep(5)  # 公式推奨の待機時間
                    operation = client.operations.get(operation)
                
                # アップロード成功
                tqdm.write(f"  ✓ アップロード完了: {original_name}")
                
                # マッピング情報を保存
                mappings[ascii_name] = {
                    'original_filename': original_name,
                    'title': file_path.stem,
                    'upload_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'operation_name': operation.name if hasattr(operation, 'name') else 'N/A',
                    'file_size': file_path.stat().st_size
                }
                
                success_count += 1
                
            except Exception as upload_error:
                error_count += 1
                tqdm.write(f"  ✗ アップロードエラー ({original_name}): {upload_error}")
                
            finally:
                # 一時ファイルを削除
                if temp_path.exists():
                    temp_path.unlink()
            
        except Exception as e:
            error_count += 1
            tqdm.write(f"\n処理エラー ({file_path.name}): {e}")
    
    # マッピング情報の保存
    save_file_mappings(mappings, mapping_file)
    
    # 結果の表示
    print(f"\n完了: {success_count}件のファイルをアップロードしました")
    if error_count > 0:
        print(f"エラー: {error_count}件のファイルで問題が発生しました")
    
    # マッピング情報から総数を表示
    print(f"File Search Store総ファイル数: {len(mappings)}件（マッピング情報より）")
    
    if len(mappings) > 0:
        print("\nアップロード済みファイル:")
        for i, (ascii_name, info) in enumerate(list(mappings.items())[:5], 1):
            original = info.get('original_filename', 'N/A')
            title = info.get('title', 'N/A')
            print(f"  {i}. {title} ({original})")
        if len(mappings) > 5:
            print(f"  ... 他 {len(mappings) - 5}件")
        print("\n✓ ファイルが正常にアップロードされました")
        print("  インデックス作成が完了するまで、数分かかる場合があります")
    
    print(f"\nファイルマッピングを保存しました: {mapping_file}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Wikipedia記事をFile Search Storeにアップロード'
    )
    parser.add_argument(
        '--data-dir',
        default='./data/wikipedia',
        help='Wikipediaのmarkdownファイルが格納されているディレクトリ (デフォルト: ./data/wikipedia)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='既存のデータをリセットしてからアップロード'
    )
    parser.add_argument(
        '--mapping-file',
        default='file_mappings.json',
        help='ファイルマッピングの保存先 (デフォルト: file_mappings.json)'
    )
    
    args = parser.parse_args()
    
    print("=== Wikipedia RAG File Search データローダー ===\n")
    print(f"データディレクトリ: {args.data_dir}\n")
    
    # データのアップロード
    upload_wikipedia_data(args.data_dir, args.reset, args.mapping_file)


if __name__ == "__main__":
    main()