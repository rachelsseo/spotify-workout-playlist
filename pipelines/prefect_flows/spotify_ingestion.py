from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta, date
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import duckdb
import time
import os
from dotenv import load_dotenv
from typing import Dict, List
import re

load_dotenv()

API_RATE_LIMIT_DELAY = 0.15
BATCH_SIZE = 500

def clean_string(s: str) -> str:
    """Clean string for deduplication"""
    if not s:
        return ""
    s = re.sub(r'[^\w\s]', '', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def get_spotify_client():
    return spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
    )

@task(retries=3, retry_delay_seconds=10)
def search_playlists(query: str, limit: int = 50) -> List[Dict]:
    """Search for playlists"""
    sp = get_spotify_client()
    time.sleep(API_RATE_LIMIT_DELAY)
    
    try:
        results = sp.search(q=query, type='playlist', limit=limit)
        playlists = []
        
        for p in results.get('playlists', {}).get('items', []):
            if not p or not p.get('id'):
                continue
            
            playlists.append({
                'playlist_id': p['id'],
                'playlist_name': p.get('name', 'Unknown'),
                'owner': p.get('owner', {}).get('display_name', 'Unknown'),
                'follower_count': p.get('followers', {}).get('total', 0),
                'total_tracks': p.get('tracks', {}).get('total', 0),
                'category': query
            })
        
        return playlists
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        return []

@task(retries=3, retry_delay_seconds=10)
def fetch_playlist_tracks(playlist_id: str) -> List[Dict]:
    """Fetch all tracks from playlist"""
    sp = get_spotify_client()
    all_tracks = []
    offset = 0
    limit = 100
    
    while True:
        time.sleep(API_RATE_LIMIT_DELAY)
        
        try:
            results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            items = results.get('items', [])
            
            if not items:
                break
            
            for item in items:
                track = item.get('track')
                if not track or not track.get('id'):
                    continue
                
                # Skip invalid durations
                duration = track.get('duration_ms', 0)
                if duration < 30000 or duration > 600000:
                    continue
                
                artists = track.get('artists', [])
                artist_name = artists[0].get('name', 'Unknown') if artists else 'Unknown'
                
                album = track.get('album', {})
                release_date = album.get('release_date', '')
                release_year = None
                
                if release_date and len(release_date) >= 4:
                    try:
                        release_year = int(release_date[:4])
                    except:
                        pass
                
                all_tracks.append({
                    'track_id': track['id'],
                    'track_name': track['name'],
                    'track_name_clean': clean_string(track['name']),
                    'artist_name': artist_name,
                    'artist_name_clean': clean_string(artist_name),
                    'album_name': album.get('name', 'Unknown'),
                    'release_year': release_year,
                    'duration_ms': duration,
                    'popularity': track.get('popularity', 0),
                    'explicit': track.get('explicit', False),
                    'playlist_id': playlist_id
                })
            
            offset += limit
            
            if len(items) < limit:
                break
                
        except Exception as e:
            print(f"Error fetching tracks: {e}")
            break
    
    return all_tracks

@task
def save_to_duckdb(playlists: List[Dict], tracks: List[Dict]):
    """Save data to DuckDB"""
    conn = duckdb.connect('data/processed/spotify.duckdb')
    
    try:
        # Save playlists
        if playlists:
            conn.executemany("""
                INSERT OR REPLACE INTO playlists 
                (playlist_id, snapshot_date, playlist_name, owner, follower_count, 
                 total_tracks, category, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'fast_collection')
            """, [(p['playlist_id'], date.today(), p['playlist_name'], p['owner'],
                   p['follower_count'], p['total_tracks'], p['category']) for p in playlists])
        
        # Save tracks
        if tracks:
            conn.executemany("""
                INSERT OR IGNORE INTO tracks 
                (track_id, track_name, track_name_clean, artist_name, artist_name_clean,
                 album_name, release_year, duration_ms, popularity, explicit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(t['track_id'], t['track_name'], t['track_name_clean'],
                   t['artist_name'], t['artist_name_clean'], t['album_name'],
                   t['release_year'], t['duration_ms'], t['popularity'], 
                   t['explicit']) for t in tracks])
            
            # Save playlist-track associations
            conn.executemany("""
                INSERT OR IGNORE INTO playlist_tracks 
                (playlist_id, track_id, snapshot_date)
                VALUES (?, ?, ?)
            """, [(t['playlist_id'], t['track_id'], date.today()) for t in tracks])
        
        conn.commit()
        
        unique = len(set([t['track_id'] for t in tracks]))
        print(f"  ✓ Saved {len(tracks)} entries ({unique} unique tracks)")
        
    finally:
        conn.close()

@flow(name="Playlist Collection", log_prints=True)
def playlist_collect():
    """Playlist collection to reach 50K+ records"""
    
    # Focused search queries (high-volume)
    queries = [
        'workout', 'gym', 'fitness', 'running', 'cardio',
        'HIIT', 'strength', 'weights', 'yoga', 'cycling',
        'exercise', 'training', 'powerlifting', 'crossfit',
        'spinning', 'pilates', 'aerobics', 'zumba'
    ]
    
    print(f"Collecting from {len(queries)} search queries...")
    print(f"Target: 200 playlists × 250 tracks = 50,000 records\n")
    
    all_playlists = []
    all_tracks = []
    
    # Collect playlists
    for query in queries:
        print(f"\nSearching: {query}")
        playlists = search_playlists(query, limit=50)
        all_playlists.extend(playlists)
    
    # Deduplicate playlists
    unique_playlists = {p['playlist_id']: p for p in all_playlists}.values()
    unique_playlists = list(unique_playlists)[:200]  # Limit to 200
    
    print(f"\n✓ Found {len(unique_playlists)} unique playlists")
    print(f"\nFetching tracks (this will take ~45-60 minutes)...\n")
    
    # Fetch tracks
    for i, playlist in enumerate(unique_playlists, 1):
        print(f"[{i}/{len(unique_playlists)}] {playlist['playlist_name'][:50]}...")
        
        tracks = fetch_playlist_tracks(playlist['playlist_id'])
        all_tracks.extend(tracks)
        
        # Save in batches
        if len(all_tracks) >= BATCH_SIZE:
            save_to_duckdb(all_playlists, all_tracks)
            all_tracks = []
        
        # Progress updates
        if i % 25 == 0:
            conn = duckdb.connect('data/processed/spotify.duckdb')
            total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
            entries = conn.execute("SELECT COUNT(*) FROM playlist_tracks").fetchone()[0]
            conn.close()
            print(f"\n  Progress: {total:,} unique tracks, {entries:,} total entries\n")
    
    # Save remaining
    if all_tracks:
        save_to_duckdb(all_playlists, all_tracks)
    
    # Final stats
    conn = duckdb.connect('data/processed/spotify.duckdb')
    stats = {
        'playlists': conn.execute("SELECT COUNT(DISTINCT playlist_id) FROM playlists").fetchone()[0],
        'tracks': conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0],
        'entries': conn.execute("SELECT COUNT(*) FROM playlist_tracks").fetchone()[0],
        'artists': conn.execute("SELECT COUNT(DISTINCT artist_name) FROM tracks").fetchone()[0]
    }
    conn.close()
    
    print("\n" + "="*70)
    print("✓ COLLECTION COMPLETE!")
    print("="*70)
    print(f"Unique tracks: {stats['tracks']:,}")
    print(f"Playlists: {stats['playlists']:,}")
    print(f"Total entries: {stats['entries']:,}")
    print(f"Unique artists: {stats['artists']:,}")
    print("="*70)

if __name__ == "__main__":
    playlist_collect()