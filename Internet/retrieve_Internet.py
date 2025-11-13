'''调用model/Internet中的接口，检索搜索到的资料'''
from typing import List, Tuple
from langchain_core.documents import Document
from model.Internet.Internet_service import retrieve


def format_docs(docs: List[Document]) -> str:
    return "\n-------------分割线--------------\n".join(doc.page_content for doc in docs if doc.page_content)


def retrieve_html(question: str) -> Tuple[List[Document], str]:
    try:
        docs = retrieve(question)
    except Exception as exc:  # noqa: BLE001 - 需要捕获所有异常以保证降级
        print(f"[internet-rag] retrieve failed: {exc}")
        return [], ""

    if not docs:
        return [], ""

    _context = format_docs(docs)
    return docs, _context
