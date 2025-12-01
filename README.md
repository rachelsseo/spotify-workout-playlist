# Creating the Perfect Workout Playlist

## Rachel Seo

### Data Source

For this project, I used the Spotify Web API to analyze workout music curation patterns across different fitness categories. I collected data from 926 public workout playlists spanning 18 different search queries (workout, gym, HIIT, yoga, running, etc.), resulting in 152,933 playlist-track associations representing 30,124 unique tracks from 7,484 artists. The data includes track metadata (name, artist, album, duration, popularity, explicit content flags) and playlist information (category, follower counts, owner details).

### Challenges / Obstacles

The primary challenge was handling API rate limits and pagination - Spotify limits requests to prevent overload, requiring implementation of retry logic with 150ms delays between calls. I also faced data quality issues including null tracks in playlist responses (when tracks are removed or become unavailable), inconsistent date formats (some release dates were year-only "2013", others "2013-05", others full "2013-05-15"), and missing artist/album metadata for certain tracks. 

I used DuckDB for analytical queries, Prefect for workflow orchestration, and pandas/matplotlib for analysis and visualization.

### Analysis

In my analysis of 152,933 records revealed interesting differences in music curation across workout types: track duration varies by 20+ seconds between categories, with high-intensity workouts (HIIT, strength training) favoring shorter tracks (215-220 seconds) for maintaining energy and providing natural break points, while low-intensity activities (yoga, stretching) prefer longer tracks (235-240 seconds) to sustain meditative flow. 

Explicit content ranges from 5-10% in yoga playlists to 40-45% in HIIT/strength playlists, clearly correlating with workout aggression rather than music quality (explicit and clean tracks show similar popularity scores). 

The data demonstrates strong recency bias - 65% of tracks are from the last 3 years - indicating curators actively refresh playlists to stay current.

The top 20 artists appear in over 4,000 playlists combined, with clear "workout music specialists" dominating the space. In terms of versatility, ~15% of tracks appear across 3+ different workout categories, suggesting certain songs have universal workout appeal regardless of fitness activity type.

### Plot / Visualization

<img width="5297" height="2953" alt="top_artists" src="https://github.com/user-attachments/assets/c1e97509-2e1c-450e-b058-6dad49e0a7f2" />

*Top 20 artists in workout music by playlist appearances (left) and track variety vs. popularity bubble chart (right). Bubble size represents playlist appearances, revealing that track count doesn't necessarily correlate with dominance - it's about having the right tracks for workout contexts.*

### GitHub Repository Link
https://github.com/rachelsseo/spotify-workout-playlist 
