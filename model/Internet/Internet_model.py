'''联网搜索的RAG检索模型类'''
from model.model_base import Modelbase
from model.model_base import ModelStatus

import os
from env import get_app_root

from langchain_community.embeddings import ModelScopeEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.document_loaders import DirectoryLoader, MHTMLLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS

from config.config import Config

# 检索模型
class InternetModel(Modelbase):
    
    _retriever: VectorStoreRetriever

    def __init__(self,*args,**krgs):
        super().__init__(*args,**krgs)

        # 此处请自行改成下载embedding模型的位置
        self._embedding_model_path =Config.get_instance().get_with_nested_params("model", "embedding", "model-name")
        self._text_splitter = RecursiveCharacterTextSplitter
        #self._embedding = OpenAIEmbeddings()
        self._embedding = ModelScopeEmbeddings(model_id=self._embedding_model_path)
        self._data_path = os.path.join(get_app_root(), "data/cache/internet")
        
        #self._logger: Logger = Logger("rag_retriever")

    # 建立向量库
    def build(self):
        try:
            html_loader = DirectoryLoader(
                self._data_path,
                glob="**/*.html",
                loader_cls=UnstructuredHTMLLoader,
                silent_errors=True,
                use_multithreading=True,
            )
            html_docs = html_loader.load()

            mhtml_loader = DirectoryLoader(
                self._data_path,
                glob="**/*.mhtml",
                loader_cls=MHTMLLoader,
                silent_errors=True,
                use_multithreading=True,
            )
            mhtml_docs = mhtml_loader.load()

            docs = html_docs + mhtml_docs
            if not docs:
                self._retriever = None
                return

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)
            if not splits:
                self._retriever = None
                return

            vectorstore = FAISS.from_documents(documents=splits, embedding=self._embedding)
            self._retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
        except Exception as exc:  # noqa: BLE001
            print(f"[internet-rag] 构建向量库失败: {exc}")
            self._retriever = None
        

        
    @property
    def retriever(self)-> VectorStoreRetriever:
        self.build()
        if self._retriever is None:
            class _EmptyRetriever:
                def invoke(self, query):  # noqa: D401 - 简单降级
                    return []

            return _EmptyRetriever()
        return self._retriever

INSTANCE = InternetModel()
