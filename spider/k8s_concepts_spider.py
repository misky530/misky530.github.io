import pandas as pd
import requests
from bs4 import BeautifulSoup


import os

url = "https://kubernetes.io/docs/concepts/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

local_html_path = "k8s_concepts.html"

def fetch_and_save_html():
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(local_html_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"已保存网页到本地: {local_html_path}")
    return response.text

def load_html():
    if os.path.exists(local_html_path):
        print(f"从本地加载网页: {local_html_path}")
        with open(local_html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return fetch_and_save_html()

html = load_html()
soup = BeautifulSoup(html, "html.parser")

# 获取网页标题
title = soup.title.string if soup.title else "No Title"
print(f"网页标题: {title}")


# 解析侧边栏菜单
def parse_sidebar_menu(soup):
    sidebar = soup.find(id="td-sidebar-menu")
    if not sidebar:
        print("未找到侧边栏菜单。"); return
    nav = sidebar.find("nav", id="td-section-nav")
    if not nav:
        print("未找到菜单导航。"); return
    def parse_ul(ul, level=1):
        items = []
        for li in ul.find_all("li", recursive=False):
            link = li.find("a", class_="td-sidebar-link")
            text = link.get_text(strip=True) if link else ""
            href = link["href"] if link and link.has_attr("href") else None
            children_ul = li.find("ul")
            children = parse_ul(children_ul, level+1) if children_ul else []
            items.append({"text": text, "href": href, "children": children})
        return items
    # 找到主菜单 ul
    ul = nav.find("ul", class_="td-sidebar-nav__section")
    menu = parse_ul(ul) if ul else []
    return menu

menu = parse_sidebar_menu(soup)
print("\nKubernetes Concepts 菜单:")

# 递归收集菜单项
def collect_menu(items, parent_url, level=1):
    rows = []
    base_url = "https://kubernetes.io"
    for item in items:
        href = item["href"] or ""
        full_url = base_url + href if href.startswith("/") else href
        rows.append({
            "标题": item["text"],
            "路径": href,
            "完整URL": full_url,
            "层级": level
        })
        if item["children"]:
            rows.extend(collect_menu(item["children"], full_url, level+1))
    return rows

if menu:
    menu_rows = collect_menu(menu, "", 1)
    df = pd.DataFrame(menu_rows)
    excel_path = "k8s_concepts_menu.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"菜单已保存为Excel: {excel_path}")
else:
    print("未解析到菜单。")
