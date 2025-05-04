import pendulum
from weread2notionpro.notion_helper import NotionHelper
from weread2notionpro.weread_api import WeReadApi
from weread2notionpro import utils
from weread2notionpro.config import book_properties_type_dict, tz
import time

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"
rating = {"poor": "⭐️", "fair": "⭐️⭐️⭐️", "good": "⭐️⭐️⭐️⭐️⭐️"}


def insert_book_to_notion(books, index, bookId):
    """插入Book到Notion"""
    """
    book 只做本次数据记录，不与远端数据混合
    """
    book = {}
    if bookId in archive_dict:
        book["书架分类"] = archive_dict.get(bookId)
    if bookId in notion_books:
        book.update(notion_books.get(bookId))
    bookInfo = weread_api.get_book_detail(bookId)

    """需要注入的属性"""
    reader = bookInfo.reader
    reading_stat = reader.get("readingStat", {})
    book_info = reader.get("bookInfo", {})
    progress = reader.get("progress", {}).get("book", {})

    markedStatus = reading_stat.get("markedStatus")
    readingProgress = progress.get("progress", 0)
    readingTime = progress.get("readingTime", 0)
    totalReadDay = utils.days_between_timestamps(
        progress.get("startReadingTime"),
        progress.get("finishTime") or time.time()
    )

    newRating = book_info.get("newRating")
    newRatingDetail = book_info.get("newRatingDetail")

    cover = book_info.get("cover", "")
    if cover:
        cover = cover.replace("/s_", "/t7_")
    if not cover or not cover.strip() or not cover.startswith("http"):
        cover = BOOK_ICON_URL

    title = book_info.get("title")
    author = book_info.get("author")
    bookId = book_info.get("bookId")
    isbn = book_info.get("isbn")
    intro = book_info.get("intro")
    categories = book_info.get("categories")

    finishedDate = progress.get("finishTime")
    lastReadingDate = progress.get("updateTime")
    beginReadingDate = progress.get("startReadTime")

    book["阅读进度"] = (
        100 if (markedStatus == 4) else readingProgress
    ) / 100
    status = "想读"
    if markedStatus == 4:
        status = "已读"
    elif readingTime >= 60:
        status = "在读"
    book["阅读状态"] = status
    book["阅读时长"] = readingTime
    book["阅读天数"] = totalReadDay
    book["评分"] = newRating
    if newRatingDetail and newRatingDetail.get("myRating"):
        book["我的评分"] = rating.get(newRatingDetail.get("myRating"))
    elif status == "已读":
        book["我的评分"] = "未评分"
    book["时间"] = (
        finishedDate
        or lastReadingDate
        or beginReadingDate
    )
    book["开始阅读时间"] = beginReadingDate
    book["最后阅读时间"] = lastReadingDate

    if bookId not in notion_books:
        book["书名"] = title
        book["BookId"] = bookId
        book["ISBN"] = isbn
        book["链接"] = weread_api.get_url(bookId)
        book["简介"] = intro
        book["作者"] = [
            notion_helper.get_relation_id(
                x, notion_helper.author_database_id, USER_ICON_URL
            )
            # TODO: 作者用空格分隔是有风险的 e.g. [美] 穆雷・N. 罗斯巴德 著
            # 考虑用另外的字段来解析
            for x in author.split(" ")
        ]
        book["封面"] = cover
        if categories:
            book["分类"] = [
                notion_helper.get_relation_id(
                    x.get("title"), notion_helper.category_database_id, TAG_ICON_URL
                )
                for x in categories
            ]
    properties = utils.get_properties(book, book_properties_type_dict)
    if book.get("时间"):
        notion_helper.get_date_relation(
            properties,
            pendulum.from_timestamp(book.get("时间"), tz="Asia/Shanghai"),
        )

    print(
        f"正在插入《{title}》,一共{len(books)}本，当前是第{index+1}本。"
    )
    parent = {"database_id": notion_helper.book_database_id,
              "type": "database_id"}
    result = None
    if bookId in notion_books:
        result = notion_helper.update_page(
            page_id=notion_books.get(bookId).get("pageId"),
            properties=properties,
            cover=utils.get_icon(cover),
        )
    else:
        result = notion_helper.create_book_page(
            parent=parent,
            properties=properties,
            icon=utils.get_icon(cover),
        )
    # page_id = result.get("id")
    # if book.get("readDetail") and book.get("readDetail").get("data"):
    #     data = book.get("readDetail").get("data")
    #     data = {item.get("readDate"): item.get("readTime") for item in data}
    #     insert_read_data(page_id, data)


def insert_read_data(page_id, readTimes):
    readTimes = dict(sorted(readTimes.items()))
    filter = {"property": "书架", "relation": {"contains": page_id}}
    results = notion_helper.query_all_by_book(
        notion_helper.read_database_id, filter)
    for result in results:
        timestamp = result.get("properties").get("时间戳").get("number")
        duration = result.get("properties").get("时长").get("number")
        id = result.get("id")
        if timestamp in readTimes:
            value = readTimes.pop(timestamp)
            if value != duration:
                insert_to_notion(
                    page_id=id,
                    timestamp=timestamp,
                    duration=value,
                    book_database_id=page_id,
                )
    for key, value in readTimes.items():
        insert_to_notion(None, int(key), value, page_id)


def insert_to_notion(page_id, timestamp, duration, book_database_id):
    parent = {"database_id": notion_helper.read_database_id,
              "type": "database_id"}
    properties = {
        "标题": utils.get_title(
            pendulum.from_timestamp(timestamp, tz=tz).to_date_string()
        ),
        "日期": utils.get_date(
            start=pendulum.from_timestamp(timestamp, tz=tz).format(
                "YYYY-MM-DD HH:mm:ss"
            )
        ),
        "时长": utils.get_number(duration),
        "时间戳": utils.get_number(timestamp),
        "书架": utils.get_relation([book_database_id]),
    }
    if page_id != None:
        notion_helper.client.pages.update(
            page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(
            parent=parent,
            icon=utils.get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )


weread_api = WeReadApi()
notion_helper = NotionHelper()
archive_dict = {}
notion_books = {}


def main():
    global notion_books
    global archive_dict
    bookshelf_books = weread_api.get_bookshelf()
    notion_books = notion_helper.get_all_book()
    bookProgress = bookshelf_books.get("bookProgress")
    bookProgress = {book.get("bookId"): book for book in bookProgress}
    for archive in bookshelf_books.get("archive"):
        name = archive.get("name")
        bookIds = archive.get("bookIds")
        archive_dict.update({bookId: name for bookId in bookIds})
    not_need_sync = []
    for key, value in notion_books.items():
        if (
            (
                key not in bookProgress
                or value.get("readingTime") == bookProgress.get(key).get("readingTime")
            )
            and (archive_dict.get(key) == value.get("category"))
            and (value.get("cover") is not None)
            and (
                value.get("status") != "已读"
                or (value.get("status") == "已读" and value.get("myRating"))
            )
        ):
            not_need_sync.append(key)
    notebooks = weread_api.get_notebooklist()
    notebooks = [d["bookId"] for d in notebooks if "bookId" in d]
    books = bookshelf_books.get("books")
    books = [d["bookId"] for d in books if "bookId" in d]
    books = list((set(notebooks) | set(books)) - set(not_need_sync))[0:1]
    for index, bookId in enumerate(books):
        insert_book_to_notion(books, index, bookId)


if __name__ == "__main__":
    main()
