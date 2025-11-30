import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


class WikipediaRAGFileSearch:
    """File Searchを使用したWikipedia RAGシステム"""
    
    def __init__(self, store_name=None):
        """RAGシステムの初期化
        
        Args:
            store_name: 既存のFile Search Store名（省略時は環境変数から取得）
        """
        # Gemini APIの設定
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")
        
        # Store名の取得（引数 > 環境変数）
        self.store_name = store_name or os.getenv("STORE_NAME")
        
        if not self.store_name:
            print("警告: STORE_NAMEが設定されていません。")
            print("data_loader_filesearch.pyでStoreを作成してください。")
    
    def generate_answer(self, query, temperature=0.7, debug=False):
        """質問に対する回答を生成
        
        Args:
            query: 質問文
            temperature: 生成の創造性（0.0〜1.0）
            debug: デバッグ情報を表示するか
            
        Returns:
            回答テキスト
        """
        if not self.store_name:
            return "エラー: File Search Storeが設定されていません。"
        
        try:
            # File Searchを使った回答生成
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[self.store_name]
                            )
                        )
                    ],
                    temperature=temperature
                )
            )
            
            # デバッグモード: レスポンス構造を出力
            if debug:
                print("\n" + "=" * 70)
                print("デバッグ情報: レスポンス構造")
                print("=" * 70)
                print(f"response type: {type(response)}")
                print(f"response attributes: {dir(response)}")
                
                if hasattr(response, 'candidates'):
                    print(f"\ncandidates count: {len(response.candidates)}")
                    if response.candidates:
                        candidate = response.candidates[0]
                        print(f"candidate type: {type(candidate)}")
                        print(f"candidate attributes: {dir(candidate)}")
                        
                        if hasattr(candidate, 'grounding_metadata'):
                            grounding = candidate.grounding_metadata
                            print(f"\ngrounding_metadata type: {type(grounding)}")
                            print(f"grounding_metadata: {grounding}")
                            print(f"grounding_metadata attributes: {dir(grounding)}")
                            
                            if hasattr(grounding, 'grounding_chunks'):
                                print(f"\ngrounding_chunks count: {len(grounding.grounding_chunks)}")
                                for i, chunk in enumerate(grounding.grounding_chunks[:3], 1):
                                    print(f"\nChunk {i}:")
                                    print(f"  type: {type(chunk)}")
                                    print(f"  attributes: {dir(chunk)}")
                                    print(f"  content: {chunk}")
                        else:
                            print("\ngrounding_metadata not found")
                
                print("=" * 70 + "\n")
            
            # 回答テキストの取得
            answer_text = response.text
            
            # 引用情報の取得
            citations = self._extract_citations(response)
            
            if citations:
                answer_text += "\n\n【引用元】\n"
                for i, citation in enumerate(citations, 1):
                    answer_text += f"{i}. {citation}\n"
            
            return answer_text
            
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
    
    def _extract_citations(self, response):
        """レスポンスから引用情報を抽出
        
        Args:
            response: Gemini APIのレスポンス
            
        Returns:
            引用情報のリスト
        """
        citations = []
        
        try:
            if not hasattr(response, 'candidates') or not response.candidates:
                return citations
            
            candidate = response.candidates[0]
            
            # grounding_metadataから引用を取得
            if hasattr(candidate, 'grounding_metadata'):
                grounding = candidate.grounding_metadata
                
                # grounding_chunksから引用を抽出
                if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                    for chunk in grounding.grounding_chunks:
                        # retrieved_contextから情報を取得
                        if hasattr(chunk, 'retrieved_context'):
                            context = chunk.retrieved_context
                            if hasattr(context, 'title'):
                                citations.append(context.title)
                            elif hasattr(context, 'uri'):
                                citations.append(context.uri)
                        # webから情報を取得（Web検索の場合）
                        elif hasattr(chunk, 'web') and chunk.web:
                            if hasattr(chunk.web, 'uri'):
                                citations.append(chunk.web.uri)
                            elif hasattr(chunk.web, 'title'):
                                citations.append(chunk.web.title)
                
                # grounding_supportsから引用を抽出（別の構造の場合）
                if hasattr(grounding, 'grounding_supports') and grounding.grounding_supports:
                    for support in grounding.grounding_supports:
                        if hasattr(support, 'segment'):
                            segment = support.segment
                            if hasattr(segment, 'text'):
                                citations.append(f"引用: {segment.text[:100]}...")
                
                # retrieval_metadataから引用を抽出
                if hasattr(grounding, 'retrieval_metadata') and grounding.retrieval_metadata:
                    metadata = grounding.retrieval_metadata
                    if hasattr(metadata, 'sources'):
                        for source in metadata.sources:
                            if hasattr(source, 'title'):
                                citations.append(source.title)
        
        except Exception as e:
            print(f"引用情報の抽出中にエラー: {e}")
        
        # 重複を削除
        return list(dict.fromkeys(citations))[:5]  # 最大5件
    
    def get_store_info(self):
        """Store情報の取得
        
        Returns:
            Store情報の辞書
        """
        if not self.store_name:
            return {
                'store_name': None,
                'status': 'not_configured'
            }
        
        # Store名が設定されていればactiveとみなす
        # (File Search APIにはStore情報取得の簡単な方法がないため)
        return {
            'store_name': self.store_name,
            'display_name': 'Wikipedia Knowledge Base',
            'status': 'active'
        }
    
    def list_files_in_store(self):
        """Store内のファイル一覧を取得（マッピング情報から）
        
        Returns:
            ファイル情報のリスト
        """
        if not self.store_name:
            return []
        
        try:
            # file_mappings.jsonから情報を取得
            import json
            mapping_file = 'file_mappings.json'
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                file_list = []
                for ascii_name, info in mappings.items():
                    file_list.append({
                        'name': ascii_name,
                        'display_name': info.get('title', 'N/A'),
                        'original_filename': info.get('original_filename', 'N/A'),
                        'size_bytes': info.get('file_size', 0),
                        'upload_date': info.get('upload_date', None)
                    })
                
                return file_list
            else:
                print("file_mappings.jsonが見つかりません")
                return []
            
        except Exception as e:
            print(f"ファイル一覧の取得中にエラー: {e}")
            return []


# 使用例
if __name__ == "__main__":
    # RAGシステムの初期化
    rag = WikipediaRAGFileSearch()
    
    # Store情報の表示
    print("=== Store情報 ===")
    store_info = rag.get_store_info()
    print(f"Store名: {store_info.get('store_name', 'N/A')}")
    print(f"表示名: {store_info.get('display_name', 'N/A')}")
    print(f"ステータス: {store_info.get('status', 'N/A')}")
    
    if store_info.get('status') == 'active':
        # ファイル一覧の表示
        print("\n=== Store内のファイル ===")
        files = rag.list_files_in_store()
        print(f"総ファイル数: {len(files)}件")
        
        # 質問応答のテスト
        print("\n=== 質問応答テスト ===")
        query = "機械学習について教えてください"
        print(f"質問: {query}")
        print("\n回答生成中...\n")
        
        answer = rag.generate_answer(query)
        print("【回答】")
        print(answer)
    else:
        print("\nStoreが設定されていないか、エラーが発生しています。")
        print("data_loader_filesearch.pyでデータをアップロードしてください。")