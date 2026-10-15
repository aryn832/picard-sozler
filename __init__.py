# Picard Sözler for Picard 3.x
# Copyright (C) 2024 Deniz Engin <dev@dilbil.im>
# License: GPL-3.0-or-later

from functools import partial


def process_response(api, file, data, reply, error):
	if error:
		return

	try:
		api.logger.debug(f"Sözler: processing response: {data}")
		instrumental = data.get("instrumental")
		if instrumental:
			api.logger.debug("Sözler: instrumental track; skipping")
			lyrics = None
		else:
			lyrics = data.get("syncedLyrics") or data.get("plainLyrics")

		if lyrics is not None:
			file.metadata["lyrics"] = lyrics
	except AttributeError:
		api.logger.error(f"Sözler: api malformed response: {data}")


def process_file(api, file):
	metadata = file.metadata
	length_ms = metadata.get("~length", 0)
	try:
		duration = int(length_ms) // 1000
	except (ValueError, TypeError):
		duration = 0

	query = {
		"artist_name": metadata.get("albumartist") or metadata.get("artist", ""),
		"album_name": metadata.get("album", ""),
		"track_name": metadata.get("title", ""),
		"duration": duration,
	}
	api.logger.debug(f"Sözler: querying API with: {query}")
	
	# Access Picard's webservice through the file object tagger
	file.tagger.webservice.get_url(
		url="https://lrclib.net/api/get",
		handler=partial(process_response, api, file),
		parse_response_type='json',
		queryargs=query,
	)


def enable(api):
	"""Entry point for Picard 3.x plugins."""
	api.register_file_post_load_processor(process_file)
