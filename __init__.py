# Picard Sözler for Picard 3.x
# License: GPL-3.0-or-later

from functools import partial
import time

def process_search_response(api, file, data, reply, error):
	if error or not isinstance(data, list) or len(data) == 0:
		api.logger.debug(f"Sözler: No search results found for {file.filename}")
		return

	best_match = data[0]
	api.logger.debug(f"Sözler: Found match '{best_match.get('trackName')}' by '{best_match.get('artistName')}'")

	instrumental = best_match.get("instrumental")
	if instrumental:
		api.logger.debug("Sözler: Instrumental track; skipping")
		return

	lyrics = best_match.get("syncedLyrics") or best_match.get("plainLyrics")
	if lyrics:
		file.metadata["lyrics"] = lyrics
		api.logger.info(f"Sözler: Successfully added lyrics to {file.filename}")


def fetch_lyrics_menu(api, files):
	for file in files:
		metadata = file.metadata
		artist = metadata.get("artist") or metadata.get("albumartist") or ""
		title = metadata.get("title") or ""
		
		if not title:
			continue

		search_query = f"{artist} {title}".strip()
		api.logger.debug(f"Sözler: Searching LRCLIB for: {search_query}")

		# Throttling to prevent HTTP 429 rate limits during batch calls
		time.sleep(0.5)

		file.tagger.webservice.get_url(
			url="https://lrclib.net/api/search",
			handler=partial(process_search_response, api, file),
			parse_response_type='json',
			queryargs={"q": search_query},
		)


def enable(api):
	"""Entry point for Picard 3.x plugins."""
	api.register_file_action("Fetch Lyrics from LRCLIB", fetch_lyrics_menu)
