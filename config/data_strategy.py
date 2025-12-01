# PLAYLIST CATEGORIES (Baseline)

WORKOUT_CATEGORIES = {
    "general_workout": {
        "search_queries": ["workout", "gym", "fitness", "training", "exercise"],
        "target_playlists": 150
    },
    "running_cardio": {
        "search_queries": ["running", "cardio", "jogging", "marathon", "treadmill", "5k", "10k"],
        "target_playlists": 120
    },
    "strength_weights": {
        "search_queries": ["weights", "powerlifting", "strength", "bodybuilding", "pump", "iron"],
        "target_playlists": 100
    },
    "hiit_intense": {
        "search_queries": ["HIIT", "intense", "crossfit", "beast mode", "hardcore", "tabata"],
        "target_playlists": 100
    },
    "yoga_stretching": {
        "search_queries": ["yoga", "stretching", "pilates", "cool down", "flexibility", "meditation"],
        "target_playlists": 80
    },
    "cycling_spinning": {
        "search_queries": ["cycling", "spinning", "peloton", "bike", "indoor cycling"],
        "target_playlists": 70
    },
    "sports_specific": {
        "search_queries": ["basketball", "soccer", "tennis", "boxing", "mma", "sports"],
        "target_playlists": 60
    },
    "dance_zumba": {
        "search_queries": ["dance workout", "zumba", "aerobics", "cardio dance"],
        "target_playlists": 50
    }
}

# Expected from playlists: 730 playlists × 60 tracks avg = ~44,000 tracks

API_RATE_LIMIT_DELAY = 0.15  # 150ms = ~6-7 req/sec (conservative)
BATCH_SIZE = 500  # Database batch insert size
MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff

# Pagination settings
SPOTIFY_MAX_LIMIT = 50  # Spotify's max per request
PLAYLIST_TRACK_LIMIT = 100  # Max tracks to fetch per playlist initially
ARTIST_TRACK_LIMIT = 50  # Top tracks per artist

# Data quality thresholds

MIN_TRACK_DURATION_MS = 30000   # 30 seconds (filter out intro/outros)
MAX_TRACK_DURATION_MS = 600000  # 10 minutes (filter out podcasts)
MIN_TRACK_POPULARITY = 0        # Include all popularity levels