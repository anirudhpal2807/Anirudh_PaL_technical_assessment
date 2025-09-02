# hubspot.py

import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# HubSpot OAuth credentials - you'll need to create these in HubSpot Developer Portal
CLIENT_ID = 'your_hubspot_client_id'  # Replace with your actual HubSpot client ID
CLIENT_SECRET = 'your_hubspot_client_secret'  # Replace with your actual HubSpot client secret
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
SCOPE = 'contacts%20oauth'  # Basic scope for contacts access

authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}'

async def authorize_hubspot(user_id, org_id):
    """Generate authorization URL for HubSpot OAuth flow"""
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)

    return f'{authorization_url}&state={encoded_state}'

async def oauth2callback_hubspot(request: Request):
    """Handle OAuth callback from HubSpot"""
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    """Retrieve stored HubSpot credentials"""
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials

def create_integration_item_metadata_object(response_json, item_type='Contact'):
    """Create IntegrationItem object from HubSpot response"""
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id'),
        type=item_type,
        name=response_json.get('properties', {}).get('firstname', '') + ' ' + response_json.get('properties', {}).get('lastname', ''),
        creation_time=response_json.get('createdAt'),
        last_modified_time=response_json.get('updatedAt'),
        url=f"https://app.hubspot.com/contacts/{response_json.get('id')}",
    )

    return integration_item_metadata

async def get_items_hubspot(credentials):
    """Retrieve HubSpot contacts and other items"""
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='No access token found in credentials.')
    
    list_of_integration_item_metadata = []
    
    # Get contacts
    try:
        contacts_response = requests.get(
            'https://api.hubapi.com/crm/v3/objects/contacts',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            params={'limit': 100}  # Limit to 100 contacts for demo
        )
        
        if contacts_response.status_code == 200:
            contacts_data = contacts_response.json()
            for contact in contacts_data.get('results', []):
                list_of_integration_item_metadata.append(
                    create_integration_item_metadata_object(contact, 'Contact')
                )
        
        # Get companies
        companies_response = requests.get(
            'https://api.hubapi.com/crm/v3/objects/companies',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            params={'limit': 50}  # Limit to 50 companies for demo
        )
        
        if companies_response.status_code == 200:
            companies_data = companies_response.json()
            for company in companies_data.get('results', []):
                company_item = IntegrationItem(
                    id=company.get('id'),
                    type='Company',
                    name=company.get('properties', {}).get('name', 'Unnamed Company'),
                    creation_time=company.get('createdAt'),
                    last_modified_time=company.get('updatedAt'),
                    url=f"https://app.hubspot.com/contacts/{company.get('id')}",
                )
                list_of_integration_item_metadata.append(company_item)
        
        # Get deals
        deals_response = requests.get(
            'https://api.hubapi.com/crm/v3/objects/deals',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            params={'limit': 50}  # Limit to 50 deals for demo
        )
        
        if deals_response.status_code == 200:
            deals_data = deals_response.json()
            for deal in deals_data.get('results', []):
                deal_item = IntegrationItem(
                    id=deal.get('id'),
                    type='Deal',
                    name=deal.get('properties', {}).get('dealname', 'Unnamed Deal'),
                    creation_time=deal.get('createdAt'),
                    last_modified_time=deal.get('updatedAt'),
                    url=f"https://app.hubspot.com/contacts/{deal.get('id')}",
                )
                list_of_integration_item_metadata.append(deal_item)
                
    except Exception as e:
        print(f"Error fetching HubSpot data: {e}")
        raise HTTPException(status_code=500, detail=f'Error fetching HubSpot data: {str(e)}')
    
    print(f'HubSpot Integration Items: {list_of_integration_item_metadata}')
    return list_of_integration_item_metadata