"""
File Search Store完全削除ユーティリティ

このスクリプトはFile Search Storeを完全に削除します。
削除後、.envのSTORE_NAMEを空にして新しいStoreを作成できます。
"""

import os
from google import genai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def delete_store_completely():
    """File Search Storeを完全に削除"""
    
    # クライアントの作成
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    store_name = os.getenv("STORE_NAME")
    
    if not store_name:
        print("エラー: .envファイルにSTORE_NAMEが設定されていません")
        return
    
    print("=" * 70)
    print("File Search Store 完全削除")
    print("=" * 70)
    print(f"\nStore名: {store_name}")
    print("\n⚠️ 警告: この操作は元に戻せません！")
    print("Store内のすべてのファイルとインデックスが削除されます。")
    
    confirm1 = input("\n本当に削除しますか？ (yes/no): ")
    if confirm1.lower() != 'yes':
        print("キャンセルしました")
        return
    
    confirm2 = input("確認: もう一度 'DELETE' と入力してください: ")
    if confirm2 != 'DELETE':
        print("キャンセルしました")
        return
    
    try:
        print("\nStoreを削除中...")
        client.file_search_stores.delete(name=store_name)
        print("✓ Storeを削除しました")
        
        # マッピングファイルも削除
        mapping_file = 'file_mappings.json'
        if os.path.exists(mapping_file):
            os.remove(mapping_file)
            print(f"✓ {mapping_file}を削除しました")
        
        print("\n" + "=" * 70)
        print("削除完了")
        print("=" * 70)
        print("\n次のステップ:")
        print("1. .envファイルを開く")
        print("2. 以下の行を見つける:")
        print(f"   STORE_NAME={store_name}")
        print("3. 以下のように変更:")
        print("   STORE_NAME=")
        print("4. data_loader_filesearch.pyを実行して新しいStoreを作成")
        
    except Exception as e:
        print(f"\nエラー: Store削除に失敗しました")
        print(f"詳細: {e}")
        print("\n可能性のある原因:")
        print("- Store名が正しくない")
        print("- すでに削除されている")
        print("- APIキーに削除権限がない")


def main():
    """メイン処理"""
    print("\n" + "=" * 70)
    print("File Search Store 完全削除ユーティリティ")
    print("=" * 70)
    
    delete_store_completely()


if __name__ == "__main__":
    main()