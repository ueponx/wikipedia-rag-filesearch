import json
from rag_system_filesearch import WikipediaRAGFileSearch


def load_file_mappings(mapping_file='file_mappings.json'):
    """ファイルマッピングを読み込み
    
    Args:
        mapping_file: マッピングファイルのパス
        
    Returns:
        マッピング辞書
    """
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def test_qa():
    """質問応答のテスト"""
    rag = WikipediaRAGFileSearch()
    
    # Store情報の確認
    store_info = rag.get_store_info()
    if store_info.get('status') != 'active':
        print("\nエラー: File Search Storeが設定されていません")
        print("data_loader_filesearch.pyでデータをアップロードしてください")
        return
    
    query = input("\n質問を入力: ").strip()
    
    if not query:
        print("質問が入力されていません")
        return
    
    # デバッグモードの選択
    debug_mode = input("デバッグモードを有効にしますか？ (y/N): ").strip().lower() == 'y'
    
    print(f"\n回答を生成中...\n")
    answer = rag.generate_answer(query, debug=debug_mode)
    
    print("=" * 60)
    print("【回答】")
    print("=" * 60)
    print(answer)
    print("=" * 60)


def interactive_mode():
    """インタラクティブモード（連続質問）"""
    rag = WikipediaRAGFileSearch()
    
    # Store情報の確認
    store_info = rag.get_store_info()
    if store_info.get('status') != 'active':
        print("\nエラー: File Search Storeが設定されていません")
        print("data_loader_filesearch.pyでデータをアップロードしてください")
        return
    
    print("\nインタラクティブモードを開始します")
    print("終了するには 'quit' または 'exit' と入力してください")
    print("デバッグモードを有効にするには 'debug on' と入力してください")
    print("=" * 60)
    
    debug_mode = False
    
    while True:
        query = input("\n質問: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("終了します")
            break
        
        if query.lower() == 'debug on':
            debug_mode = True
            print("デバッグモードを有効にしました")
            continue
        
        if query.lower() == 'debug off':
            debug_mode = False
            print("デバッグモードを無効にしました")
            continue
        
        if not query:
            continue
        
        print("\n回答を生成中...\n")
        answer = rag.generate_answer(query, debug=debug_mode)
        
        print("-" * 60)
        print(answer)
        print("-" * 60)


def show_statistics():
    """統計情報の表示"""
    rag = WikipediaRAGFileSearch()
    
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    
    # Store情報
    store_info = rag.get_store_info()
    print(f"\n【Store情報】")
    print(f"  Store名: {store_info.get('store_name', 'N/A')}")
    print(f"  表示名: {store_info.get('display_name', 'N/A')}")
    print(f"  ステータス: {store_info.get('status', 'N/A')}")
    
    if store_info.get('status') == 'active':
        # ファイル一覧（マッピング情報から）
        print(f"\n【Store内のファイル】")
        files = rag.list_files_in_store()
        print(f"  総ファイル数: {len(files)}件")
        
        if files:
            print(f"\n  最近のファイル（最大5件）:")
            for i, file_info in enumerate(files[:5], 1):
                display_name = file_info.get('display_name', 'N/A')
                original = file_info.get('original_filename', 'N/A')
                size_kb = file_info.get('size_bytes', 0) / 1024
                print(f"    {i}. {display_name}")
                print(f"       元ファイル: {original} ({size_kb:.1f}KB)")
        
        # マッピング情報
        mappings = load_file_mappings()
        if mappings:
            print(f"\n【ファイルマッピング情報】")
            print(f"  マッピング総数: {len(mappings)}件")
            print(f"\n  マッピングサンプル（最大3件）:")
            for i, (ascii_name, info) in enumerate(list(mappings.items())[:3], 1):
                original = info.get('original_filename', 'N/A')
                title = info.get('title', 'N/A')
                upload_date = info.get('upload_date', 'N/A')
                print(f"    {i}. {title}")
                print(f"       元ファイル: {original}")
                print(f"       アップロード日: {upload_date}")
    else:
        print("\nStoreが設定されていないか、エラーが発生しています")
        if store_info.get('error'):
            print(f"エラー詳細: {store_info.get('error')}")
    
    print("=" * 60)


def show_file_mappings():
    """ファイルマッピング一覧の表示"""
    print("\n" + "=" * 60)
    print("ファイルマッピング一覧")
    print("=" * 60)
    
    mappings = load_file_mappings()
    
    if not mappings:
        print("\nファイルマッピング情報が見つかりません")
        print("data_loader_filesearch.pyでデータをアップロードしてください")
        return
    
    print(f"\n総数: {len(mappings)}件\n")
    
    for i, (ascii_name, info) in enumerate(mappings.items(), 1):
        original = info.get('original_filename', 'N/A')
        title = info.get('title', 'N/A')
        upload_date = info.get('upload_date', 'N/A')
        
        print(f"{i}. {title}")
        print(f"   元ファイル名: {original}")
        print(f"   ASCII名: {ascii_name}")
        print(f"   アップロード日: {upload_date}")
        print()
    
    print("=" * 60)


def main():
    """メインメニュー"""
    while True:
        print("\n" + "=" * 60)
        print("Wikipedia RAG File Search システム - テストメニュー")
        print("=" * 60)
        print("1. 質問応答テスト")
        print("2. インタラクティブモード（連続質問）")
        print("3. 統計情報の表示")
        print("4. ファイルマッピング一覧")
        print("5. 終了")
        print("=" * 60)
        
        choice = input("\n選択 (1-5): ").strip()
        
        if choice == '1':
            test_qa()
        elif choice == '2':
            interactive_mode()
        elif choice == '3':
            show_statistics()
        elif choice == '4':
            show_file_mappings()
        elif choice == '5':
            print("\n終了します")
            break
        else:
            print("\n無効な選択です")


if __name__ == "__main__":
    # 初期確認
    rag = WikipediaRAGFileSearch()
    store_info = rag.get_store_info()
    
    if store_info.get('status') != 'active':
        print("\n" + "=" * 60)
        print("⚠️  注意")
        print("=" * 60)
        print("\nFile Search Storeが設定されていません")
        print("先にdata_loader_filesearch.pyを実行してください:")
        print("\n  $ python data_loader_filesearch.py")
        print("\n" + "=" * 60)
        
        proceed = input("\nそれでもテストメニューを起動しますか？ (y/N): ").strip()
        if proceed.lower() != 'y':
            print("終了します")
            exit(0)
    
    # メインメニューを起動
    main()