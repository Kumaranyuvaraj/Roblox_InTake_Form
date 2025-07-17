#!/usr/bin/env python3
"""
Standalone Roblox API Test Script

This script tests the Roblox API endpoints independently without Django dependencies.
Run with: python test_roblox_api.py
"""

import time
import requests
import json
from datetime import datetime


def search_roblox_user(username):
    """Search for a Roblox user by username"""
    try:
        print(f"Searching for Roblox user: {username}")
        url = "https://users.roblox.com/v1/usernames/users"
        
        data = {
            "usernames": [username],
            "excludeBannedUsers": False
        }

        response = requests.post(url, json=data)
        time.sleep(0.6)  # Rate limiting

        if response.status_code == 429:
            return {'error': 'Rate limit exceeded. Please try again later.'}
    
        response.raise_for_status()
        search_data = response.json()

        results = []
        
        for user in search_data.get('data', []):
            user_id = user['id']
            print(f"Found user ID: {user_id}")
            
            # Get detailed user info
            user_url = f"https://users.roblox.com/v1/users/{user_id}"
            user_response = requests.get(user_url)
            time.sleep(0.6)  # Rate limiting

            if user_response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            
            user_response.raise_for_status()
            player_data = user_response.json()
            results.append(player_data)

        return results
    
    except requests.RequestException as e:
        return {'error': f'An error occurred while fetching player data: {str(e)}'}


def get_user_by_id(user_id):
    """Get Roblox user details by user ID"""
    try:
        print(f"Getting user details for ID: {user_id}")
        url = f"https://users.roblox.com/v1/users/{user_id}"
        
        response = requests.get(url)
        time.sleep(0.6)  # Rate limiting

        if response.status_code == 429:
            return {'error': 'Rate limit exceeded. Please try again later.'}
        
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException as e:
        return {'error': f'An error occurred while fetching user data: {str(e)}'}


def get_user_avatar(user_id):
    """Get user avatar information"""
    try:
        print(f"Getting avatar for user ID: {user_id}")
        url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        
        response = requests.get(url)
        time.sleep(0.6)  # Rate limiting

        if response.status_code == 429:
            return {'error': 'Rate limit exceeded. Please try again later.'}
        
        response.raise_for_status()
        return response.json()
    
    except requests.RequestException as e:
        return {'error': f'An error occurred while fetching avatar data: {str(e)}'}


def test_roblox_api():
    """Test various Roblox API endpoints"""
    print("=" * 50)
    print("ROBLOX API TEST SCRIPT")
    print("=" * 50)
    
    # Test 1: Search for a user
    test_username = input("Enter a Roblox username to test (or press Enter for 'Builderman'): ").strip()
    if not test_username:
        test_username = "Mialo"
    
    print(f"\nTest 1: Searching for user '{test_username}'")
    print("-" * 30)
    
    search_results = search_roblox_user(test_username)
    
    if 'error' in search_results:
        print(f"Error: {search_results['error']}")
        return
    
    if not search_results:
        print("No users found!")
        return
    
    print(f"Found {len(search_results)} user(s):")
    for i, user in enumerate(search_results):
        print(f"\nUser {i+1}:")
        print(f"  ID: {user.get('id')}")
        print(f"  Username: {user.get('name')}")
        print(f"  Display Name: {user.get('displayName')}")
        print(f"  Description: {user.get('description', 'No description')}")
        print(f"  Created: {user.get('created')}")
        print(f"  Is Banned: {user.get('isBanned', False)}")
        
        # Test 2: Get avatar for this user
        user_id = user.get('id')
        if user_id:
            print(f"\nTest 2: Getting avatar for user ID {user_id}")
            print("-" * 30)
            
            avatar_data = get_user_avatar(user_id)
            if 'error' in avatar_data:
                print(f"Avatar Error: {avatar_data['error']}")
            else:
                avatar_info = avatar_data.get('data', [])
                if avatar_info:
                    print(f"  Avatar URL: {avatar_info[0].get('imageUrl', 'Not available')}")
                    print(f"  State: {avatar_info[0].get('state', 'Unknown')}")
        
        print("-" * 30)
    
    print("\nAPI Test Complete!")


if __name__ == "__main__":
    try:
        test_roblox_api()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
