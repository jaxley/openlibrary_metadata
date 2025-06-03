# -*- coding: utf-8 -*-

# metadata query plugin for openlibrary.org

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2022 quarz12
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from typing import List, Optional
import urllib.parse
import dateparser

import requests

# try:
#     import cchardet  # optional for better speed
# except ImportError:
#     pass

# from time import time
# from operator import itemgetter
from calibreweb.cps.services.Metadata import MetaRecord, MetaSourceInfo, Metadata
import calibreweb.cps.logger as logger

log = logger.create()

# search API https://openlibrary.org/dev/docs/api/search
# https://openlibrary.org/search.json?q=the+lord+of+the+rings

"""_summary_

Returns:
    _type_: _description_
"""

search_fields = [
    "key",
    "title",
    "subtitle",
    "author_name",
    "cover_i",
    "ratings_average",
    "first_publish_year",
    "description",
    "editions",
    "editions.key",
    "editions.title",
    "editions.description",
    "editions.language",
    "editions.isbn",
    "editions.publish_date",
    "editions.publisher_facet",
]


class OpenLibrary(Metadata):
    __name__ = "OpenLibrary"
    __id__ = "openlibrary"
    metasourceinfo = MetaSourceInfo(
        id=__id__,
        description=__name__,
        link="https://openlibrary.org",
    )
    headers = {"accept": "application/json"}
    session = requests.Session()
    session.headers = headers

    def search(
        self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[List[MetaRecord]]:

        # TODO: user-agent header with name and email.
        def get_work_details(work_id: str) -> dict:
            with self.session as session:
                try:
                    r = session.get(f"https://openlibrary.org/works/{work_id}.json")
                    r.raise_for_status()
                    return r.json()
                except Exception as ex:
                    log.warning(ex)
                    return {}

        def get_edition_details(edition_id: str) -> dict:
            with self.session as session:
                try:
                    r = session.get(f"https://openlibrary.org/works/{edition_id}.json")
                    r.raise_for_status()
                    return r.json()
                except Exception as ex:
                    log.warning(ex)
                    return {}

        # description: Optional[str] = ""
        # series: Optional[str] = None
        # series_index: Optional[Union[int, float]] = 0
        # identifiers: Dict[str, Union[str, int]] = dataclasses.field(default_factory=dict)
        # publisher: Optional[str] = None
        # publishedDate: Optional[str] = None
        # rating: Optional[int] = 0
        # languages: Optional[List[str]] = dataclasses.field(default_factory=list)
        # tags: Optional[List[str]] = dataclasses.field(default_factory=list)

        def build_metarecord(doc: dict):
            work_deets = get_work_details(doc.get("key").split("/")[-1])
            description = (
                (work_deets['description']['value'] if
                    'value' in work_deets['description'] else work_deets['description'])
                if "description" in work_deets
                else None
            )
            edition1_key = (
                doc["editions"]["docs"][0]["key"].split("/")[-1]
                if "editions" in doc
                and "docs" in doc["editions"]
                and len(doc["editions"]["docs"]) > 0
                else None
            )
            edition_deets = get_edition_details(edition1_key)
            publish_date = edition_deets.get("publish_date")
            publisher = (
                edition_deets.get("publishers")[0]
                if "publishers" in edition_deets
                and len(edition_deets["publishers"]) > 0
                else None
            )
            series = edition_deets['series'][0].split(',')[0] if "series" in edition_deets else None
            series_index = (edition_deets['series'][0].split(',')[1].replace(' #', '') if "series" in edition_deets and 
                len(edition_deets['series']) > 0 and len(edition_deets['series'][0].split(',')) == 2 else None)
            if series_index:
                series_index = int(series_index) if not "." in series_index else float(series_index)

            identifiers = {}
            if "isbn_10" in edition_deets and len(edition_deets["isbn_10"]) > 0:
                identifiers["isbn_10"] = edition_deets["isbn_10"][0]
            if "isbn_13" in edition_deets and len(edition_deets["isbn_13"]) > 0:
                identifiers["isbn_13"] = edition_deets["isbn_13"][0]

            if (
                edition1_key
                and "ia" in doc["editions"]["docs"][0]
                and len(doc["editions"]["docs"][0]["ia"]) > 0
            ):
                identifiers["ia"] = doc["editions"]["docs"][0]["ia"][0]

            return MetaRecord(
                id=doc.get("key").split("/")[-1],
                title=doc.get("title"),
                authors=doc.get("author_name"),
                url=f"https://openlibrary.org{work_deets.get('key')}",
                source=OpenLibrary.metasourceinfo,
                cover=self.resolve_redirect_url(
                    f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg"
                ),
                description=description,
                series=series,
                series_index=series_index,
                identifiers=identifiers,
                publisher=publisher,
                # publish_date is NOT consistently formatted. Using a magic parser.
                publishedDate=dateparser.parse(publish_date).strftime('%Y-%m-%d') if isinstance(publish_date, str) else None,
                rating=f"{doc.get('ratings_average')}",
                tags="",
            )

        if self.active:
            try:
                results = self.session.get(
                    (
                        f"https://openlibrary.org/search.json?limit=20&fields={','.join(search_fields)}&q={urllib.parse.quote_plus(query)}"
                    ),
                    headers=self.headers,
                )
                results.raise_for_status()
            
                records = map(build_metarecord, results.json()["docs"])
                return list(records)
            except requests.exceptions.HTTPError as e:
                log.error_or_exception(e)
                return []
            except Exception as e:
                log.warning(e)
                return []

    # open library uses URL redirects but calibre-web doesn't follow them. Resolve the final URL to use.
    def resolve_redirect_url(self, url):
        response = requests.get(url, timeout=(10, 200))
        return response.url
