#!/usr/bin/env python3
"""
Test Spotify Web API connection and explore available data
(WITHOUT audio features)

This script verifies:
1. Authentication works
2. We can search for playlists
3. We can fetch track data
4. We can get artist information
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import json
from pprint import pprint

# Load environment variables
load_dotenv()

def test_authentication():
    """Test basic authentication"""
    print("="*70)
    print("STEP 1: Testing Authentication")
    print("="*70)
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Verify credentials exist
    if not client_id or not client_secret:
        print("✗ ERROR: Missing credentials in .env file")
        print("\n  Make sure your .env file contains:")
        print("  SPOTIFY_CLIENT_ID=your_client_id")
        print("  SPOTIFY_CLIENT_SECRET=your_client_secret")
        return None
    
    print(f"✓ Client ID found: {client_id[:10]}...")
    print(f"✓ Client Secret found: {client_secret[:10]}...")
    
    try:
        # Create Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test authentication by making a simple search
        test_search = sp.search(q='workout', type='playlist', limit=1)
        
        print("\n✓ Authentication successful!")
        print("✓ API connection working!")
        return sp
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Check that your credentials are correct")
        print("  2. Make sure there are no extra spaces in .env file")
        print("  3. Try regenerating your Client Secret in Spotify Dashboard")
        return None

def explore_workout_playlists(sp):
    """Explore workout playlists to understand data structure"""
    print("\n" + "="*70)
    print("STEP 2: Exploring Workout Playlists")
    print("="*70)
    
    try:
        # Search for workout playlists
        results = sp.search(q='workout', type='playlist', limit=10)
        
        if not results or 'playlists' not in results:
            print("✗ No results returned from search")
            return None
        
        playlists = results['playlists']['items']
        
        if not playlists:
            print("✗ No playlists found")
            return None
        
        print(f"\n✓ Found {len(playlists)} workout playlists")
        
        print("\nSample playlists:")
        for i, playlist in enumerate(playlists[:5], 1):
            if not playlist:
                continue
                
            name = playlist.get('name', 'Unknown')
            owner = playlist.get('owner', {})
            owner_name = owner.get('display_name', 'Unknown') if owner else 'Unknown'
            tracks_info = playlist.get('tracks', {})
            track_count = tracks_info.get('total', 0) if tracks_info else 0
            playlist_id = playlist.get('id', 'Unknown')
            description = playlist.get('description', 'No description')
            followers = playlist.get('followers', {}).get('total', 0)
            
            print(f"\n{i}. {name}")
            print(f"   Owner: {owner_name}")
            print(f"   Tracks: {track_count}")
            print(f"   Followers: {followers:,}")
            print(f"   ID: {playlist_id}")
            print(f"   Description: {description[:80]}...")
        
        # Return first valid playlist for further exploration
        for playlist in playlists:
            if playlist and playlist.get('id'):
                return playlist
        
        print("✗ No valid playlists found")
        return None
        
    except Exception as e:
        print(f"✗ Error searching playlists: {e}")
        import traceback
        traceback.print_exc()
        return None

def explore_playlist_tracks(sp, playlist):
    """Get tracks from a playlist and examine structure"""
    print("\n" + "="*70)
    print("STEP 3: Exploring Playlist Tracks")
    print("="*70)
    
    try:
        playlist_id = playlist.get('id')
        playlist_name = playlist.get('name', 'Unknown')
        
        if not playlist_id:
            print("✗ Playlist ID is missing")
            return []
        
        print(f"\nAnalyzing playlist: {playlist_name}")
        
        # Get tracks from playlist
        results = sp.playlist_tracks(playlist_id, limit=10)
        
        if not results or 'items' not in results:
            print("✗ No tracks returned")
            return []
        
        items = results['items']
        print(f"\n✓ Retrieved {len(items)} tracks")
        
        tracks = []
        print("\nSample tracks:")
        
        for i, item in enumerate(items[:5], 1):
            if not item or 'track' not in item:
                continue
                
            track = item['track']
            
            if not track:  # Track can be None (deleted/unavailable)
                print(f"\n{i}. [Unavailable track]")
                continue
            
            # Safely extract track info
            track_name = track.get('name', 'Unknown')
            track_id = track.get('id')
            
            # Get artist (tracks can have multiple artists)
            artists = track.get('artists', [])
            artist_name = artists[0].get('name', 'Unknown') if artists else 'Unknown'
            artist_id = artists[0].get('id') if artists else None
            
            # Get album
            album = track.get('album', {})
            album_name = album.get('name', 'Unknown') if album else 'Unknown'
            release_date = album.get('release_date', 'Unknown') if album else 'Unknown'
            
            duration_ms = track.get('duration_ms', 0)
            popularity = track.get('popularity', 0)
            explicit = track.get('explicit', False)
            
            print(f"\n{i}. {track_name}")
            print(f"   Artist: {artist_name}")
            print(f"   Album: {album_name}")
            print(f"   Release Date: {release_date}")
            print(f"   Duration: {duration_ms / 1000:.0f} seconds ({duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d})")
            print(f"   Popularity: {popularity}/100")
            print(f"   Explicit: {'Yes' if explicit else 'No'}")
            if track_id:
                print(f"   Track ID: {track_id}")
                if artist_id:
                    print(f"   Artist ID: {artist_id}")
                tracks.append(track)
            else:
                print(f"   Track ID: None (skipping)")
        
        return tracks
        
    except Exception as e:
        print(f"✗ Error getting playlist tracks: {e}")
        import traceback
        traceback.print_exc()
        return []

def explore_artist_data(sp, tracks):
    """Get artist information - genres, popularity, followers"""
    print("\n" + "="*70)
    print("STEP 4: Exploring Artist Data")
    print("="*70)
    
    if not tracks:
        print("✗ No tracks available to analyze")
        return []
    
    print("\nFetching artist details...")
    
    artist_data = []
    
    for track in tracks[:3]:  # Just check first 3 to save API calls
        artists = track.get('artists', [])
        if not artists:
            continue
        
        artist_id = artists[0].get('id')
        if not artist_id:
            continue
        
        try:
            artist = sp.artist(artist_id)
            
            print(f"\n{artist['name']}")
            print(f"   Genres: {', '.join(artist.get('genres', ['Unknown']))}")
            print(f"   Popularity: {artist.get('popularity', 0)}/100")
            print(f"   Followers: {artist.get('followers', {}).get('total', 0):,}")
            
            artist_data.append({
                'artist_id': artist['id'],
                'artist_name': artist['name'],
                'genres': artist.get('genres', []),
                'popularity': artist.get('popularity', 0),
                'followers': artist.get('followers', {}).get('total', 0)
            })
            
        except Exception as e:
            print(f"✗ Error fetching artist {artist_id}: {e}")
            continue
    
    return artist_data

def save_sample_data(playlist, tracks, artists):
    """Save sample data as JSON for inspection"""
    print("\n" + "="*70)
    print("STEP 6: Saving Sample Data")
    print("="*70)
    
    sample_data = {
        'playlist': {
            'id': playlist.get('id'),
            'name': playlist.get('name'),
            'owner': playlist.get('owner', {}).get('display_name'),
            'followers': playlist.get('followers', {}).get('total', 0),
            'total_tracks': playlist.get('tracks', {}).get('total', 0),
            'description': playlist.get('description', '')
        },
        'tracks': [],
        'artists': artists
    }
    
    for track in tracks:
        if track and track.get('id'):
            sample_data['tracks'].append({
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown',
                'album': track['album']['name'] if track.get('album') else 'Unknown',
                'release_date': track['album'].get('release_date') if track.get('album') else None,
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'explicit': track['explicit']
            })
    
    # Save to file
    os.makedirs('data/raw', exist_ok=True)
    with open('data/raw/sample_data.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"\n✓ Saved sample data to data/raw/sample_data.json")
    print(f"  Playlist data: 1 playlist")
    print(f"  Tracks: {len(sample_data['tracks'])}")
    print(f"  Artists: {len(sample_data['artists'])}")
    
    print("\nYou can inspect this file to see the exact data structure.")

def main():
    """Run all exploration steps"""
    print("\n" + "="*70)
    print("SPOTIFY WORKOUT PLAYLIST ANALYZER - API EXPLORATION")
    print("="*70)
    print("Testing what data we can access WITHOUT audio features API")
    print("="*70)
    
    # Step 1: Authenticate
    sp = test_authentication()
    if not sp:
        print("\n✗ Setup failed. Please check your credentials and try again.")
        return
    
    # Step 2: Explore playlists
    playlist = explore_workout_playlists(sp)
    if not playlist:
        print("\n✗ Could not retrieve playlists. Stopping here.")
        return
    
    # Step 3: Explore tracks
    tracks = explore_playlist_tracks(sp, playlist)
    if not tracks:
        print("\n✗ Could not retrieve tracks. Stopping here.")
        return
    
    # Step 4: Explore artist data
    artists = explore_artist_data(sp, tracks)
    
    # Step 5: Save sample data
    save_sample_data(playlist, tracks, artists)
    
    print("\n" + "="*70)
    print("✓ API EXPLORATION COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    main()