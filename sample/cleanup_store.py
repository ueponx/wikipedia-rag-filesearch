#!/usr/bin/env python3
"""
File Search Store削除ツール

使い方:
  python cleanup.py <store_name>
  python cleanup.py fileSearchStores/wikipediaknowledgebase-abc123xyz456

引数を指定しない場合：
  1. .envファイルのSTORE_NAMEを使用
  2. STORE_NAMEがない場合は利用可能なStoreのリストを表示
"""

import os
import sys
import time
from dotenv import load_dotenv
from google import genai

def list_stores(client):
    """利用可能なStoreのリストを取得して表示"""
    
    print("\n" + "="*70)
    print("利用可能なFile Search Storeを取得中...")
    print("="*70 + "\n")
    
    try:
        stores = list(client.file_search_stores.list())
        
        if not stores:
            print("❌ 利用可能なStoreが見つかりませんでした")
            print("\n次のいずれかを実行してください:")
            print("  1. main.pyを実行して新しいStoreを作成")
            print("  2. Google AI Studioで既存のStoreを確認")
            return None
        
        print(f"✅ {len(stores)}個のStoreが見つかりました:\n")
        
        # Storeリストを表示
        for i, store in enumerate(stores, 1):
            # ドキュメント数を取得（可能であれば）
            doc_count = "不明"
            try:
                if hasattr(store, 'active_document_count'):
                    doc_count = store.active_document_count
            except:
                pass
            
            # 作成日時を取得（可能であれば）
            created = "不明"
            try:
                if hasattr(store, 'create_time'):
                    created = str(store.create_time)[:19]  # 日時部分のみ
            except:
                pass
            
            print(f"  [{i}] {store.display_name}")
            print(f"      Store名: {store.name}")
            print(f"      ドキュメント数: {doc_count}")
            print(f"      作成日時: {created}")
            print()
        
        return stores
        
    except Exception as e:
        print(f"❌ Storeリストの取得に失敗しました: {e}")
        return None


def select_store_interactively(stores):
    """対話的にStoreを選択"""
    
    print("-" * 70)
    print("削除するStoreを選択してください")
    print("-" * 70)
    
    while True:
        choice = input(f"\n番号を入力 (1-{len(stores)}) または 'q' で終了: ").strip()
        
        if choice.lower() == 'q':
            print("\n削除をキャンセルしました")
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(stores):
                selected_store = stores[index]
                print(f"\n選択されたStore: {selected_store.name}")
                return selected_store.name
            else:
                print(f"❌ 1から{len(stores)}の間の数値を入力してください")
        except ValueError:
            print("❌ 数値または 'q' を入力してください")


def delete_store_with_documents(client, store_name):
    """Store内の全ドキュメントを削除してからStoreを削除"""
    
    print(f"\n{'='*70}")
    print(f"Store削除処理: {store_name}")
    print(f"{'='*70}\n")
    
    try:
        # Step 1: Store内のドキュメント一覧を取得
        print("Step 1: Store内のドキュメントを取得中...")
        try:
            documents = list(client.file_search_stores.documents.list(
                parent=store_name
            ))
            doc_count = len(documents)
            print(f"  → {doc_count}個のドキュメントが見つかりました")
        except Exception as e:
            print(f"  ⚠️  ドキュメント一覧の取得に失敗: {e}")
            print(f"  → Storeが既に存在しないか、空の可能性があります")
            documents = []
        
        # Step 2: 各ドキュメントを削除（config={'force': True}で関連Chunksも削除）
        if documents:
            print(f"\nStep 2: {doc_count}個のドキュメント（および関連データ）を削除中...")
            for i, doc in enumerate(documents, 1):
                try:
                    print(f"  [{i}/{doc_count}] 削除中: {doc.name}")
                    # config={'force': True}を指定してChunksも一緒に削除
                    client.file_search_stores.documents.delete(
                        name=doc.name,
                        config={'force': True}
                    )
                    print(f"  ✅ 削除完了（関連データを含む）")
                except Exception as e:
                    print(f"  ⚠️  削除失敗: {e}")
                    # エラーがあっても続行
                
                # API制限を避けるため少し待機
                if i < doc_count:
                    time.sleep(0.5)
            
            print(f"\n  → 全ドキュメントの削除処理が完了しました")
        else:
            print("\nStep 2: スキップ（削除するドキュメントがありません）")
        
        # Step 3: Storeを削除（config={'force': True}で念のため）
        print(f"\nStep 3: Storeを削除中...")
        try:
            # config={'force': True}を指定して残存Documentsも削除
            client.file_search_stores.delete(
                name=store_name,
                config={'force': True}
            )
            print(f"  ✅ Store削除完了!")
            return True
        except Exception as e:
            print(f"  ❌ Store削除失敗: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False


def main():
    # .envファイルから環境変数を読み込む
    load_dotenv()
    
    # クライアントの作成
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEYが.envファイルに設定されていません")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    # Store名を取得（コマンドライン引数または.envから）
    store_name = None
    
    if len(sys.argv) > 1:
        # コマンドライン引数で指定された場合
        store_name = sys.argv[1]
        print(f"\n引数で指定されたStore: {store_name}")
    else:
        # .envのSTORE_NAMEを確認
        store_name = os.getenv("STORE_NAME")
        
        if store_name:
            print(f"\n.envから読み込んだStore: {store_name}")
        else:
            # STORE_NAMEもない場合は、Storeリストを表示
            print("\n引数もSTORE_NAMEも指定されていません")
            stores = list_stores(client)
            
            if not stores:
                sys.exit(1)
            
            # 対話的に選択
            store_name = select_store_interactively(stores)
            
            if not store_name:
                sys.exit(0)
    
    # 削除確認
    print("\n" + "="*70)
    print("⚠️  WARNING: この操作は元に戻せません!")
    print("="*70)
    print(f"\n削除対象: {store_name}")
    print("\n以下が削除されます:")
    print("  - Store内の全ドキュメント（インデックスデータ）")
    print("  - Storeそのもの")
    
    confirm = input("\n本当に削除しますか? 'DELETE' と入力してください: ")
    
    if confirm != 'DELETE':
        print("\n削除がキャンセルされました")
        print("何も削除されませんでした")
        sys.exit(0)
    
    # 削除実行
    success = delete_store_with_documents(client, store_name)
    
    if success:
        print("\n" + "="*70)
        print("✅ 削除が完了しました!")
        print("="*70)
        print("\n次のステップ:")
        print("  1. .envファイルからSTORE_NAMEを削除またはコメントアウト")
        print("  2. 必要に応じてmain.pyを実行して新しいStoreを作成")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ 削除処理中にエラーが発生しました")
        print("="*70)
        print("\n考えられる原因:")
        print("  - Storeが既に削除されている")
        print("  - Store名が間違っている")
        print("  - APIキーが無効")
        print("  - ネットワーク接続の問題")
        sys.exit(1)


if __name__ == "__main__":
    main()