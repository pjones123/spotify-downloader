"""
Preload module for the console.
"""

import json
import concurrent.futures
from pathlib import Path

from typing import List

from spotdl.download.downloader import Downloader
from spotdl.utils.search import parse_query


def preload(
    query: List[str],
    downloader: Downloader,
    save_path: Path,
) -> None:
    """
    Use audio provider to find the download links for the songs
    and save them to the disk.

    ### Arguments
    - query: list of strings to search for.
    - downloader: Already initialized downloader instance.
    - save_path: Path to the file to save the metadata to.

    ### Notes
    - This function is multi-threaded.
    """

    # Parse the query
    songs = parse_query(query, downloader.threads)

    save_data = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=downloader.threads
    ) as executor:
        future_to_song = {
            executor.submit(downloader.search, song): song for song in songs
        }
        for future in concurrent.futures.as_completed(future_to_song):
            song = future_to_song[future]
            try:
                data, _ = future.result()
                if data is None:
                    downloader.progress_handler.error(
                        f"Could not find a match for {song.display_name}"
                    )
                    continue

                downloader.progress_handler.log(
                    f"Found url for {song.display_name}: {data}"
                )
                save_data.append({**song.json, "download_url": data})
            except Exception as exc:
                downloader.progress_handler.error(
                    f"{song} generated an exception: {exc}"
                )

    # Save the songs to a file
    with open(save_path, "w", encoding="utf-8") as save_file:
        json.dump(save_data, save_file, indent=4, ensure_ascii=False)

    downloader.progress_handler.log(
        f"Saved {len(save_data)} song{'s' if len(save_data) > 1 else ''} to {save_path}"
    )