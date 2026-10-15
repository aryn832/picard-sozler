# Picard Sözler is a plugin that fetches lyrics from a public API.
# Copyright (C) 2024 Deniz Engin <dev@dilbil.im>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

PLUGIN_NAME = "Picard Sözler"
PLUGIN_AUTHOR = "Deniz Engin <dev@dilbil.im>"
PLUGIN_DESCRIPTION = "Sözler is a lyrics fetcher for Picard. It uses the public API provided by the lrclib.net project, which requires no registration or API keys! The API provides synced lyrics and unsynced ones as a fallback. We prioritize the synced ones."
PLUGIN_VERSION = "0.0.3"
PLUGIN_API_VERSIONS = ["2.1", "3.0"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0-standalone.html"

from functools import partial
import json

from picard.file import register_file_post_load_processor
from picard import log


def log_debug(s):
	log.debug(f"{PLUGIN_NAME}: {s}")


def log_err(s):
	log.error(f"{PLUGIN_NAME}: {s}")


def process_response(file, data, reply, error):
	if error:
		return

	try:
		log_debug("starting to process")
		log_debug(f"got response: {data}")
		instrumental = data.get("instrumental")
		if instrumental:
			log_debug("instrumental track; skipping")
			lyrics = None
		else:
			# Fallbacks to plain, ie, unsynced lyrics.
			lyrics = data.get("syncedLyrics") or data.get("plainLyrics")

		if lyrics is not None:
			file.metadata["lyrics"] = lyrics
	except AttributeError:
		log_err(f"api malformed response: {data}")


def process_file(file):
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
	log_debug(f"trying to query with: {query}")
	file.tagger.webservice.get_url(
		url="https://lrclib.net/api/get",
		handler=partial(process_response, file),
		parse_response_type='json',
		queryargs=query,
	)


register_file_post_load_processor(process_file)
