# Picard Sözler for Picard 3.x
# License: GPL-3.0-or-later

from functools import partial
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QNetworkRequest

from picard.plugin3.api import BaseAction

# LRCLIB strictly requires identifying your client via User-Agent and Lrclib-Client headers
LRCLIB_HEADERS = {
    "User-Agent": "PicardSozler/1.0.0 (https://github.com/erin/picard-sozler)",
    "Lrclib-Client": "PicardSozler/1.0.0"
}


def process_search_response(api, file, queue, data, reply, error):
    http_status = (
        reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply
        else None
    )

    if http_status in (429, 503):
        header_bytes = reply.rawHeader(b"Retry-After") if reply else None
        retry_str = bytes(header_bytes).decode("utf-8", errors="ignore") if header_bytes else ""
        delay_sec = int(retry_str) if retry_str.isdigit() else 10

        api.logger.warning(
            f"Sözler: Rate limited (HTTP {http_status}) for {file.filename}. Pausing for {delay_sec}s..."
        )
        queue.insert(0, file)
        QTimer.singleShot(delay_sec * 1000, lambda: process_next_in_queue(api, queue))
        return

    if error or not isinstance(data, list) or len(data) == 0:
        api.logger.debug(f"Sözler: No search results found for {file.filename}")
        QTimer.singleShot(1000, lambda: process_next_in_queue(api, queue))
        return

    best_match = data[0]
    api.logger.debug(
        f"Sözler: Found match '{best_match.get('trackName')}' by '{best_match.get('artistName')}'"
    )

    if not best_match.get("instrumental"):
        lyrics = best_match.get("syncedLyrics") or best_match.get("plainLyrics")
        if lyrics:
            file.metadata["lyrics"] = lyrics
            api.logger.info(f"Sözler: Successfully added lyrics to {file.filename}")

    QTimer.singleShot(1000, lambda: process_next_in_queue(api, queue))


def process_next_in_queue(api, queue):
    if not queue:
        api.logger.info("Sözler: Finished processing all queued tracks.")
        return

    file = queue.pop(0)
    metadata = file.metadata
    artist = metadata.get("artist") or metadata.get("albumartist") or ""
    title = metadata.get("title") or ""

    if not title:
        process_next_in_queue(api, queue)
        return

    search_query = f"{artist} {title}".strip()
    api.logger.debug(f"Sözler: Searching LRCLIB for: {search_query}")

    file.tagger.webservice.get_url(
        url="https://lrclib.net/api/search",
        handler=partial(process_search_response, api, file, queue),
        parse_response_type="json",
        queryargs={"q": search_query},
        headers=LRCLIB_HEADERS,
    )


class FetchLyricsAction(BaseAction):
    NAME = "Fetch Lyrics from LRCLIB"
    TITLE = "Fetch Lyrics from LRCLIB"

    def callback(self, objs):
        if not isinstance(objs, (list, tuple)):
            objs = [objs]

        file_queue = []
        for obj in objs:
            files = getattr(obj, "files", [obj])
            for file in files:
                if hasattr(file, "metadata"):
                    file_queue.append(file)

        if file_queue:
            self.api.logger.info(f"Sözler: Starting sequential queue for {len(file_queue)} file(s).")
            process_next_in_queue(self.api, file_queue)


def enable(api):
    """Entry point for Picard 3.x plugins."""
    api.register_track_action(FetchLyricsAction)
