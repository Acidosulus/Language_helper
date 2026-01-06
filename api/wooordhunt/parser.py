import re
import urllib
import urllib.request
import requests
from pathlib import Path
from bs4 import BeautifulSoup as BS
import ssl


def reduce(lc_source: str):
    return (
        lc_source.replace("                ", " ")
        .replace("                ", " ")
        .replace("        ", " ")
        .replace("        ", " ")
        .replace("    ", " ")
        .replace("    ", " ")
        .replace("  ", " ")
        .replace("  ", " ")
        .replace("  ", " ")
    )


def cleanhtml(raw_html):
    cleantext = re.sub(re.compile("<.*?>"), "", raw_html)
    return cleantext


def find_from(lc_source: str, lc_search: str, index=1):
    val = -1
    for i in range(0, index):
        val = lc_source.find(lc_search, val + 1)
    return val


def sx(source_string="", left_split="", right_split="", index=1):
    if source_string.count(left_split) < index:
        return ""
    lc_str = source_string
    for i in range(0, index):
        lc_str = lc_str[lc_str.find(left_split) + len(left_split) : len(lc_str)]
    return lc_str[0 : lc_str.find(right_split)]


def download_file(url: str, path):
    print(f"{url} ===> {path}")
    lc_local_file_name = path
    r = requests.get(url, stream=True, verify=False)
    if r.status_code == 200:
        with open(lc_local_file_name, "wb") as f:
            for chunk in r:
                f.write(chunk)


class Wooordhunt:
    def __init__(self, lc_link: str):
        context = ssl._create_unverified_context()
        self.context = sx(
            urllib.request.urlopen(lc_link, context=context)
            .read()
            .decode("UTF-8")
            + "||||||",
            '<div id="header">',
            "||||||",
        )
        self.sound_path = sx(
            self.context,
            '<audio id="audio_us" preload="auto"> <source src="',
            '"',
        )
        if len(self.sound_path) > 5:
            path_for_sounds = (
                Path(__file__).resolve().parent.parent / "static" / "sounds"
            )
            print(f"path_for_sounds:{path_for_sounds}")

            # пока ничего не качаем
            # download_file(r'http://wooordhunt.ru'+self.sound_path, path_for_sounds / sx((self.sound_path+'|')[::-1], '|', '/')[::-1])

    def get_transcription(self):
        lc_str = sx(
            self.context, 'class="transcription">', "</span> <audio"
        ).replace(" ", "")
        if "<" in lc_str:
            lc_str = "|" + sx(lc_str, "|", "|") + "|"
        return lc_str

    def get_path_on_mp3(self):
        return "https://wooordhunt.ru" + sx(
            self.context,
            '<audio id="audio_us" preload="auto"> <source src="',
            '"',
        )

    def get_translation(self):
        lc_result_str = sx(self.context, '<div class="t_inline_en">', "</div>")
        lc_from = "<h4 class="
        lc_to = '<div class="gap"></div>'
        lc_result = lc_from + sx(
            self.context.replace("<br/>", chr(13)), lc_from, lc_to
        ).replace("+7", chr(13))
        lc_result = cleanhtml(lc_result)
        lc_result = (
            lc_result.replace("&ensp;", " ")
            .replace("&#8595;", "")
            .replace("Мои примеры", "")
            .replace("<h4 class=", "")
        )
        lc_result = lc_result.replace("глагол - ", "- ").replace(
            "глагол- ", "- "
        )
        lc_result = lc_result.replace("прилагательное -", "- ").replace(
            "прилагательное-", "- "
        )
        lc_result = lc_result.replace("наречие- ", "- ").replace(
            "наречие - ", "- "
        )
        lc_result = lc_result.replace("существительное-", "- ").replace(
            "существительное -", "- "
        )
        return reduce(lc_result_str + chr(13) + lc_result)

    def get_examples(self):
        lc_result = ""
        soup = BS(self.context, features="html5lib")
        original = soup.find_all("p", {"class": "ex_o"})
        translate = soup.find_all("p", {"class": "ex_t"})
        examples = []
        for i in range(min(len(original), len(translate))):
            examples.append(
                {
                    "example": original[i].text.strip(),
                    "translate": translate[i].text.strip(),
                }
            )
        return examples


def only_english_paragraphs(pc_str: str):
    lc_russian = "йцукенгшщзхъфывапролджэячсмитьбюё"
    lc_russian = lc_russian + lc_russian.upper()
    lc_result = ""

    lb_now_english = False
    for lc_chr in pc_source:
        if lb_now_english == False and lc_chr in lc_russian:
            pass  # сейчас не английский и текущая буква не английская - просто подолжаем

        if (
            lb_now_english == True and lc_chr in lc_russian
        ):  # был английский, но, теперь он кончился
            pass

        if lc_chr in lc_russian:
            lc_result = (
                lc_result
                + '<span class = "'
                + lc_style_name
                + '">'
                + lc_chr
                + "</span>"
            )
        else:
            lc_result = lc_result + lc_chr
    return lc_result


# удаляет их строки все символы не подходящите для имени файла
def Delete_from_String_all_Characters_Unsuitable_For_FileName(pc: str):
    lc_suitable_simbols = "qwertyuiopasdfghjklzxcvbnm,.1234567890-!"
    lc_suitable_simbols = (
        lc_suitable_simbols + lc_suitable_simbols.upper() + " "
    )
    lc_result = ""
    for ch in pc:
        if ch in lc_suitable_simbols:
            lc_result = lc_result + ch
    return lc_result.strip()


if False:
    lo_wh = Wooordhunt(r"https://wooordhunt.ru/word/quench")
    open("source.html", "w", encoding="utf8").write(lo_wh.context)
    print("========================================= transcription")
    print(lo_wh.get_transcription())
    open("transcription.html", "w", encoding="utf8").write(
        lo_wh.get_transcription()
    )
    print("========================================= path_on_mp3")
    print(lo_wh.get_path_on_mp3())
    print("========================================= translation")
    print(lo_wh.get_translation())
    open("translation.html", "w", encoding="utf8").write(
        lo_wh.get_translation()
    )
    print("========================================= examples")
    print(lo_wh.get_examples())
    open("examples.html", "w", encoding="utf8").write(lo_wh.get_examples())
    print("=========================================")
