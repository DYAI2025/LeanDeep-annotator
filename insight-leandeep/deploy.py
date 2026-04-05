#!/usr/bin/env python3
"""
Hostinger Deploy Script — Upload static files via Hostinger API

Usage:
    python3 deploy.py --api-key YOUR_KEY --api-email YOUR_EMAIL --account-id YOUR_ACCOUNT_ID

Environment variables can be used instead of CLI args:
    HOSTINGER_API_KEY, HOSTINGER_API_EMAIL, HOSTINGER_ACCOUNT_ID
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local
load_dotenv('.env.local')

HOSTINGER_API_BASE = "https://api.hostinger.com/v1"

class HostingerDeployer:
    def __init__(self, api_key, api_email, account_id):
        self.api_key = api_key
        self.api_email = api_email
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_ftp_credentials(self):
        """Retrieve FTP credentials for the account"""
        url = f"{HOSTINGER_API_BASE}/accounts/{self.account_id}/ftp"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()
    
    def upload_files(self, local_path='./'):
        """
        Upload all HTML/CSS/JS files from local path.
        Note: Hostinger API may not support direct file uploads.
        Alternative: Use FTP or SSH via returned credentials.
        """
        print(f"📦 Preparing files from: {local_path}")
        
        # Find all relevant files
        files_to_upload = []
        for ext in ['*.html', '*.js', '*.css']:
            files_to_upload.extend(Path(local_path).glob(ext))
        
        print(f"✅ Found {len(files_to_upload)} files to upload:")
        for f in files_to_upload:
            print(f"   - {f.name}")
        
        # For now, return file list (FTP/SCP would be needed for actual upload)
        return files_to_upload
    
    def create_subdomain(self, subdomain='insight', domain='leandeep.de'):
        """Create subdomain via Hostinger API (if available)"""
        url = f"{HOSTINGER_API_BASE}/accounts/{self.account_id}/domains"
        
        payload = {
            'subdomain': subdomain,
            'domain': domain,
            'document_root': f'/public_html/{subdomain}.{domain}'
        }
        
        try:
            resp = self.session.post(url, json=payload)
            resp.raise_for_status()
            print(f"✅ Subdomain {subdomain}.{domain} created!")
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"⚠️  Subdomain {subdomain}.{domain} already exists.")
            else:
                print(f"❌ Error creating subdomain: {e}")
            return None
    
    def deploy(self, subdomain='insight', domain='leandeep.de', local_path='./'):
        """Main deploy flow"""
        print(f"\n🚀 Deploying {subdomain}.{domain} to Hostinger...")
        print(f"📧 API Email: {self.api_email}")
        print(f"🔑 Account ID: {self.account_id}\n")
        
        # Step 1: Create subdomain
        self.create_subdomain(subdomain, domain)
        
        # Step 2: Upload files
        files = self.upload_files(local_path)
        
        print(f"\n📝 Next steps:")
        print(f"   1. Use FTP/SFTP to upload files to /public_html/{subdomain}.{domain}/")
        print(f"   2. Or use Hostinger File Manager in the dashboard")
        print(f"   3. Verify at: https://{subdomain}.{domain}")
        print(f"\n✅ Deployment preparation complete!")


def main():
    parser = argparse.ArgumentParser(description='Deploy to Hostinger via API')
    parser.add_argument('--api-key', default=os.getenv('HOSTINGER_API_KEY'))
    parser.add_argument('--api-email', default=os.getenv('HOSTINGER_API_EMAIL'))
    parser.add_argument('--account-id', default=os.getenv('HOSTINGER_ACCOUNT_ID'))
    parser.add_argument('--subdomain', default='insight')
    parser.add_argument('--domain', default='leandeep.de')
    parser.add_argument('--local-path', default='./')
    
    args = parser.parse_args()
    
    # Validate required credentials
    if not all([args.api_key, args.api_email, args.account_id]):
        print("❌ Missing credentials!")
        print("   Set HOSTINGER_API_KEY, HOSTINGER_API_EMAIL, HOSTINGER_ACCOUNT_ID")
        print("   Or use: python3 deploy.py --api-key ... --api-email ... --account-id ...")
        sys.exit(1)
    
    deployer = HostingerDeployer(args.api_key, args.api_email, args.account_id)
    deployer.deploy(args.subdomain, args.domain, args.local_path)


if __name__ == '__main__':
    main()
