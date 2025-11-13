from Internet.Internet_prompt import extract_question
from Internet.retrieve_Internet import retrieve_html
from client.clientfactory import Clientfactory
from env import get_app_root

import os
import re
import shutil
import threading
from typing import Dict

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

_SAVE_PATH = os.path.join(get_app_root(), "data/cache/internet")
_REQUEST_TIMEOUT = 8
_DETAIL_TIMEOUT = 10
_LINKS_LOCK = threading.Lock()


def _safe_filename(title: str, max_len: int = 80) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]+", "_", title)
    sanitized = sanitized.strip().strip(".")
    if not sanitized:
        sanitized = "page"
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    return sanitized


def _write_html_file(title: str, content: str, link_map: Dict[str, str], url: str) -> None:
    safe_name = _safe_filename(title)
    filepath = os.path.join(_SAVE_PATH, f"{safe_name}.html")
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(_SAVE_PATH, f"{safe_name}_{counter}.html")
        counter += 1

    with open(filepath, "w", encoding="utf-8") as file_obj:
        file_obj.write(content)

    with _LINKS_LOCK:
        link_map[url] = title


def InternetSearchChain(question, history):
    if os.path.exists(_SAVE_PATH):
        shutil.rmtree(_SAVE_PATH)

    if not os.path.exists(_SAVE_PATH):
        os.makedirs(_SAVE_PATH)

    whole_question = extract_question(question, history)
    question_list = re.split(r"[;；]", whole_question)

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    threads = []
    links: Dict[str, str] = {}

    # 为每个问题创建单独的线程
    for question in question_list:
        # 每个线程执行搜索操作
        thread = threading.Thread(target=search_bing, args=(question, links, 3))
        threads.append(thread)
        thread.start()
        thread = threading.Thread(target=search_baidu, args=(question, links, 3))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    docs_available = False
    _context = ""
    if has_html_files(_SAVE_PATH):
        try:
            docs, _context = retrieve_html(question)
            docs_available = bool(docs)
        except Exception as exc:  # noqa: BLE001
            print(f"[internet-rag] retrieve_html failed: {exc}")

    if docs_available and _context:
        prompt = (
            f"根据你现有的知识，辅助以搜索到的文件资料：\n{_context}\n 回答问题：\n{question}\n 尽可能多的覆盖到文件资料"
        )
    else:
        prompt = question

    response = Clientfactory().get_client().chat_with_ai_stream(prompt)

    return response, links, bool(links)


def search_bing(query, links, num_results=3):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, compress",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0",
    }
    search_urls = [
        "https://cn.bing.com/search",
        "https://www.bing.com/search",
    ]
    for search_url in search_urls:
        flag = 0
        try:
            response = requests.get(
                search_url,
                headers=headers,
                params={"q": query},
                timeout=_REQUEST_TIMEOUT,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"请求 {search_url} 失败：{exc}")
            continue

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.find_all("li", class_="b_algo"):
                if flag >= num_results:
                    break
                title = item.find("h2").text
                link = item.find("a")["href"].split("#")[0]  # 删除 '#' 后的部分

                try:
                    response = requests.get(link, timeout=_DETAIL_TIMEOUT)
                    if response.status_code == 200 and response.text:
                        _write_html_file(title, response.text, links, link)
                        flag += 1
                        print(f"下载成功: {link}")
                    else:
                        print(
                            f"下载 {link} 失败，状态码 {response.status_code}"
                        )
                except Exception as exc:  # noqa: BLE001
                    print(f"下载 {link} 出错: {exc}")
            # 检查是否达到了期望的结果数
            if flag < num_results:
                print("访问bing失败，请检查网络代理")
        else:
            print("访问 Bing 失败，状态码:", response.status_code)


def search_baidu(query, links, num_results=3):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, compress",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0",
    }
    base_url = "https://www.baidu.com/s"

    flag = 0
    try:
        response = requests.get(
            base_url,
            headers=headers,
            params={"wd": query},
            timeout=_REQUEST_TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"请求百度失败：{exc}")
        return

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # 百度搜索结果的条目
        for item in soup.find_all("div", class_="result"):
            if flag >= num_results:
                break
            try:
                title = item.find("h3").text
                link = item.find("a")["href"].split("#")[0]

                try:
                    response = requests.get(link, timeout=_DETAIL_TIMEOUT)
                    if response.status_code == 200 and response.text:
                        _write_html_file(title, response.text, links, link)
                        flag += 1
                        print(f"下载成功: {link}")
                    else:
                        print(
                            f"下载 {link} 失败，状态码 {response.status_code}"
                        )
                except Exception as exc:  # noqa: BLE001
                    print(f"下载 {link} 出错: {exc}")
            except Exception as exc:  # noqa: BLE001
                print(f"解析百度搜索结果条目失败: {exc}")

        # 检查是否达到了期望的结果数
        if flag < num_results:
            print("访问百度失败，请检查网络环境")
    else:
        print("Error: ", response.status_code)


def has_html_files(directory_path):
    if os.path.exists(directory_path):
        # 遍历目录中的文件
        for file_name in os.listdir(directory_path):
            if file_name.endswith(".html"):
                return True
        return False
    else:
        return False
