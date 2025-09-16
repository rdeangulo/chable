#!/usr/bin/env python3
"""
Script to check Cloudinary images and update fotos.json
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Cloudinary configuration
CLOUD_NAME = "ds3cng4pl"  # From your existing JSON
BASE_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/resources/image"

def get_recent_images(api_key: str, api_secret: str, days_back: int = 7) -> List[Dict]:
    """
    Fetch recent images from Cloudinary
    """
    # Calculate timestamp for recent uploads
    since_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
    
    params = {
        'api_key': api_key,
        'timestamp': int(datetime.now().timestamp()),
        'max_results': 100,
        'type': 'upload',
        'resource_type': 'image'
    }
    
    # For now, let's try to get all images and filter by recent ones
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            resources = data.get('resources', [])
            
            # Filter for recent uploads
            recent_images = []
            for resource in resources:
                created_at = resource.get('created_at', '')
                if created_at:
                    # Convert Cloudinary timestamp to datetime
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if created_dt > datetime.now() - timedelta(days=days_back):
                        recent_images.append(resource)
            
            return recent_images
        else:
            print(f"Error fetching images: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_image_structure(images: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the structure of images to understand what's new
    """
    analysis = {
        'by_residence': {},
        'by_type': {},
        'new_images': []
    }
    
    for image in images:
        public_id = image.get('public_id', '')
        url = image.get('secure_url', '')
        created_at = image.get('created_at', '')
        
        # Extract residence and type from public_id
        parts = public_id.split('/')
        if len(parts) >= 2:
            residence = parts[0] if parts[0] != 'residencias' else parts[1] if len(parts) > 1 else 'unknown'
            image_type = parts[-2] if len(parts) > 1 else 'unknown'
        else:
            residence = 'unknown'
            image_type = 'unknown'
        
        # Categorize by residence
        if residence not in analysis['by_residence']:
            analysis['by_residence'][residence] = []
        analysis['by_residence'][residence].append({
            'public_id': public_id,
            'url': url,
            'type': image_type,
            'created_at': created_at
        })
        
        # Categorize by type
        if image_type not in analysis['by_type']:
            analysis['by_type'][image_type] = []
        analysis['by_type'][image_type].append({
            'public_id': public_id,
            'url': url,
            'residence': residence,
            'created_at': created_at
        })
        
        analysis['new_images'].append({
            'public_id': public_id,
            'url': url,
            'residence': residence,
            'type': image_type,
            'created_at': created_at
        })
    
    return analysis

def update_fotos_json(analysis: Dict[str, Any], json_file_path: str = "assets/fotos.json"):
    """
    Update the fotos.json file with new images
    """
    try:
        # Load existing JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            fotos_data = json.load(f)
        
        # Update with new images
        for image in analysis['new_images']:
            residence = image['residence']
            image_type = image['type']
            url = image['url']
            
            # Skip if residence is unknown or not in our structure
            if residence == 'unknown' or residence not in fotos_data.get('residencias', {}):
                continue
            
            # Ensure the structure exists
            if 'fotos' not in fotos_data['residencias'][residence]:
                fotos_data['residencias'][residence]['fotos'] = {}
            
            if image_type not in fotos_data['residencias'][residence]['fotos']:
                fotos_data['residencias'][residence]['fotos'][image_type] = []
            
            # Check if this image already exists
            existing_urls = [img['url'] for img in fotos_data['residencias'][residence]['fotos'][image_type]]
            if url not in existing_urls:
                # Add new image
                new_image = {
                    "url": url,
                    "descripcion": f"{image_type.title()} de la residencia {residence.upper()}",
                    "tipo": image_type
                }
                fotos_data['residencias'][residence]['fotos'][image_type].append(new_image)
                print(f"Added new {image_type} image for {residence}: {url}")
        
        # Save updated JSON
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(fotos_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated {json_file_path} successfully!")
        
    except Exception as e:
        print(f"Error updating JSON: {e}")

def main():
    """
    Main function to check and update images
    """
    print("🔍 Checking Cloudinary for new images...")
    
    # You'll need to set these environment variables or provide them
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Please set CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET environment variables")
        print("You can get these from your Cloudinary dashboard")
        return
    
    # Get recent images
    recent_images = get_recent_images(api_key, api_secret, days_back=7)
    
    if not recent_images:
        print("No recent images found in the last 7 days")
        return
    
    print(f"Found {len(recent_images)} recent images")
    
    # Analyze the structure
    analysis = analyze_image_structure(recent_images)
    
    # Print analysis
    print("\n📊 Analysis:")
    print(f"By residence: {list(analysis['by_residence'].keys())}")
    print(f"By type: {list(analysis['by_type'].keys())}")
    
    for residence, images in analysis['by_residence'].items():
        print(f"\n🏠 {residence.upper()}:")
        for img in images:
            print(f"  - {img['type']}: {img['public_id']}")
    
    # Update JSON file
    update_fotos_json(analysis)

if __name__ == "__main__":
    main()
