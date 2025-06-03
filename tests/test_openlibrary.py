import json
import os
import sys
import re
from typing import Tuple

import pytest

# from unittest import mock
import responses
from responses import matchers

from calibreweb.cps.services.Metadata import MetaRecord
from metadata.openlibrary import OpenLibrary, search_fields

# Add calibreweb to sys.path, so we "import cps" works locally like it does when script is installed
for path in sys.path:
    if path.endswith("site-packages"):
        sys.path.append(os.path.join(path, "calibreweb"))


@responses.activate
def test_search_populates_data():
    query = {"q": "lord of the rings", "fields": ",".join(search_fields), "limit": "20"}

    responses.get(
        "https://openlibrary.org/search.json",
        json=load_test_json_data_file("lotr-search.json"),
        status=200,
        content_type="application/json",
        match=[matchers.query_param_matcher(query)],
    )

    urlpattern = re.compile(r"https://covers.openlibrary.org/b/id/.*", flags=0)
    responses.get(
        url=urlpattern,
        status=301,
        headers={
            "Location": "https://archive.org/download/olcovers708/olcovers708-L.zip/7083706-L.jpg"
        },
        content_type="text/html",
    )

    responses.get(
        "https://archive.org/download/olcovers708/olcovers708-L.zip/7083706-L.jpg",
        status=200,
        content_type="image/jpeg",
    )

    responses.get(
        "https://openlibrary.org/works/OL51711484M.json",
        status=200,
        json=load_test_json_data_file("OL51711484M.json")
    )

    works_pattern = re.compile(r"https://openlibrary.org/works/[^.]+\.json")
    responses.get(
        url=works_pattern,
        status=200,
        json=load_test_json_data_file("OL27448W.json")
    )

    ol = OpenLibrary()
    lotr = ol.search(query=query['q'])

    assert len(responses.calls) == 401
    assert len(lotr) > 0
    eq_result = object_equals(
        lotr[0],
        MetaRecord(
            id="OL27448W",
            title="The Lord of the Rings",
            authors=["J.R.R. Tolkien"],
            url="https://openlibrary.org/works/OL27448W",
            source=OpenLibrary.metasourceinfo,
            cover="https://archive.org/download/olcovers708/olcovers708-L.zip/7083706-L.jpg",
            description=(
                "Originally published from 1954 through 1956, J.R.R. Tolkien's richly complex series ushered "
                "in a new age of epic adventure storytelling. A philologist and illustrator who took inspiration "
                "from his work, Tolkien invented the modern heroic quest novel from the ground up, creating not "
                "just a world, but a domain, not just a lexicon, but a language, that would spawn countless "
                "imitators and lead to the inception of the epic fantasy genre. Today, THE LORD OF THE RINGS"
                " is considered \"the most influential fantasy novel ever written.\" (THE ENCYCLOPEDIA OF FANTASY)"
                "\r\n\r\nDuring his travels across Middle-earth, the hobbit Bilbo Baggins had found the Ring. But "
                "the simple band of gold was far from ordinary; it was in fact the One Ring - the greatest of the "
                "ancient Rings of Power. Sauron, the Dark Lord, had infused it with his own evil magic, and when "
                "it was lost, he was forced to flee into hiding.\r\n\r\nBut now Sauron's exile has ended and his "
                "power is spreading anew, fueled by the knowledge that his treasure has been found. He has gathered "
                "all the Great Rings to him, and will stop at nothing to reclaim the One that will complete his "
                "dominion. The only way to stop him is to cast the Ruling Ring deep into the Fire-Mountain at the "
                "heart of the land of Mordor--Sauron's dark realm.\r\n\r\nFate has placed the burden in the hands of "
                "Frodo Baggins, Bilbo's heir...and he is resolved to bear it to its end. Or his own. \r\n\r\n\r\n"
                "----------\r\n\r\n\r\n**Contains**\r\n\r\n - [The Fellowship of the Ring][1]\r\n - "
                "[The Two Towers][2]\r\n - [The Return of the King][3]\r\n - [The Lord of the Rings [2/2]]"
                "(https://openlibrary.org/works/OL27306128W)\r\n - [The Lord of the Rings [1/6]]"
                "(https://openlibrary.org/works/OL24170898W)\r\n - [The Lord of the Rings [1/9]]"
                "(https://openlibrary.org/works/OL27305953W)\r\n - [The Lord of the Rings [2/9]]"
                "(https://openlibrary.org/works/OL27305892W)\r\n - [The Lord of the Rings [3/9]]"
                "(https://openlibrary.org/works/OL27306048W)\r\n\r\n\r\n\r\n  [1]: "
                "https://openlibrary.org/works/OL14933414W/The_Fellowship_of_the_Ring\r\n  [2]: "
                "https://openlibrary.org/works/OL27479W/The_Two_Towers\r\n  [3]: "
                "https://openlibrary.org/works/OL27516W/The_Return_of_the_King"
            ),
            series=None,
            series_index=None,
            identifiers={'isbn_10': '0618343997', 'ia': 'lordofrings00tolk_5'},
            publisher="Houghton Mifflin Company",
            publishedDate="2003-06-02",
            rating="4.5172415",
            tags="",
        ),
    )
    assert eq_result[0], eq_result[1]

    return

@responses.activate
def test_populates_series():
    query = {"q": "all systems red", "fields": ",".join(search_fields), "limit": "20"}

    responses.get(
        "https://openlibrary.org/search.json",
        json=load_test_json_data_file("asr-search.json"),
        status=200,
        content_type="application/json",
        match=[matchers.query_param_matcher(query)],
    )

    responses.get(
        "https://openlibrary.org/works/OL26818660M.json",
        json=load_test_json_data_file("OL26818660M.json"),
        status=200,
        content_type="application/json",
    )

    responses.get(
        "https://openlibrary.org/works/OL17914663W.json",
        json=load_test_json_data_file("OL17914663W.json"),
        status=200,
        content_type="application/json",
    )

    responses.get(
        'https://covers.openlibrary.org/b/id/9157148-L.jpg',
        status=200,
        content_type='image/jpeg'
    )

    ol = OpenLibrary()
    asr = ol.search(query=query['q'])

    assert len(asr) > 0
    assert asr[0].series == "The Murderbot Diaries"
    assert asr[0].series_index == 1

@responses.activate
def test_empty_search_json():
    query = {"q": "foo", "fields": ",".join(search_fields), "limit": "20"}

    responses.get(
        "https://openlibrary.org/search.json",
        json={},
        status=200,
        content_type="application/json",
        match=[matchers.query_param_matcher(query)],
    )

    ol = OpenLibrary()
    results = ol.search(query=query['q'])

    assert results == []

@responses.activate
def test_search_missing_fields():
    response = {"start": 0,
    "numFoundExact": True,
    "num_found": 33,
    "documentation_url": "https://openlibrary.org/dev/docs/api/search",
    "q": "foo",
    "offset": None,
    "docs": [
        {
            "author_name": None,
            "editions": [
                {"doc": {}}
            ]
        }]
    }

    query = {"q": "foo", "fields": ",".join(search_fields), "limit": "20"}

    responses.get(
        "https://openlibrary.org/search.json",
        json=response,
        status=200,
        content_type="application/json",
        match=[matchers.query_param_matcher(query)],
    )

    ol = OpenLibrary()
    results = ol.search(query=query['q'])

    assert results == []


def object_equals(object1: object, object2: object) -> Tuple[bool, str]:
    """compares two objects by their properties

    Args:
        object1 (object): first object to compare
        object2 (object): second object to compare to first

    Returns:
        Tuple[bool,str]: result of the comparison and a string containing a
        reason the comparison failed
    """
    vars1 = vars(object1)
    vars2 = vars(object2)
    for key in vars1:
        if vars1[key] != vars2[key]:
            return False, f"Values for {key} do not match: {vars1[key]} != {vars2[key]}"
    return True, ""


def load_test_json_data_file(filename: str) -> str:
    """Loads a JSON file from tests/data.
    Returns the data loaded as JSON

    Args:
        filename (str): the name of the file in tests/data

    Returns:
        str: the file contents as JSON
    """
    test_dir = os.path.dirname(__file__)
    with open(os.path.join(test_dir, "data", filename), "r", encoding="utf8") as file:
        data = json.load(file)
    return data


if __name__ == "__main__":
    pytest.main()
