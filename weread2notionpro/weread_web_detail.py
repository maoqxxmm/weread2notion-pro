import requests
import os
import re
from dataclasses import dataclass
from typing import Optional, TypedDict

# 从环境变量获取 Cookie 字符串
cookie_str = os.getenv('WEREAD_COOKIE')  # 假设环境变量为 COOKIE_STR

# 直接设置请求头
headers = {
    'Cookie': cookie_str
}


class NewRatingDetail(TypedDict):
    myRating: int
    title: str


class Category(TypedDict):
    title: str


class AuthorSeg(TypedDict):
    words: str
    highlight: int
    authorId: Optional[str]


class ReaderBookInfo(TypedDict):
    title: str
    author: str
    cover: str
    intro: str
    newRating: int
    newRatingDetail: NewRatingDetail
    isbn: str
    bookId: str
    categories: list[Category]
    authorSeg: Optional[list[AuthorSeg]]
    finishReading: int


class ReaderProgressBook(TypedDict):
    updateTime: int
    readingTime: int
    progress: int
    startReadingTime: int
    finishTime: Optional[int]


class ReaderProgress(TypedDict):
    book: ReaderProgressBook


class ReaderReadingStatus(TypedDict):
    markedStatus: int


class BookDetailReader(TypedDict):
    infoId: str
    bookId: str
    bookInfo: ReaderBookInfo
    progress: ReaderProgress
    readingStat: ReaderReadingStatus


@dataclass
class BookDetail:
    reader: BookDetailReader


def get_book_detail(url: str):
    # 发送请求
    response = requests.get(
        url,
        headers=headers
    )

    # 使用正则表达式提取 window 对象数据（例如 window.myData = {...};）
    pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*\(function\(\)'
    match = re.search(pattern, response.text, re.DOTALL)

    if match:
        data_str = match.group(1)
        # 如果需要解析为 Python 对象（如字典）：
        import json
        data = json.loads(data_str)
        return BookDetail(data.get("reader"))
    else:
        raise Exception("未找到目标数据")


if __name__ == '__main__':
    print(get_book_detail('https://weread.qq.com/web/reader/6bf3215071a123016bf0b74'))
