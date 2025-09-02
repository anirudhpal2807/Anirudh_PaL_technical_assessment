# VectorShift Integrations Technical Assessment

## 📋 Project Overview

This is a full-stack application that implements OAuth integrations with multiple platforms (HubSpot, Notion, Airtable) using React frontend and FastAPI backend. The project demonstrates OAuth 2.0 flow implementation, data retrieval from third-party APIs, and a modern web interface for managing integrations.

## 🏗️ Architecture

- **Frontend**: React.js with Material-UI components
- **Backend**: FastAPI (Python) with async/await support
- **Database**: Redis (with in-memory fallback)
- **Authentication**: OAuth 2.0 for all integrations
- **API**: RESTful API design with proper error handling

## 📁 Project Structure

```
integrations_technical_assessment/
├── backend/
│   ├── integrations/
│   │   ├── airtable.py          # Airtable OAuth integration
│   │   ├── notion.py            # Notion OAuth integration
│   │   ├── hubspot.py           # HubSpot OAuth integration (NEW)
│   │   └── integration_item.py  # Data model for integration items
│   ├── main.py                  # FastAPI application
│   ├── redis_client.py          # Redis client with in-memory fallback
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── integrations/
│   │   │   ├── airtable.js      # Airtable frontend component
│   │   │   ├── notion.js        # Notion frontend component
│   │   │   └── hubspot.js       # HubSpot frontend component (NEW)
│   │   ├── App.js               # Main React app
│   │   ├── integration-form.js  # Integration selection form
│   │   └── data-form.js         # Data loading form
│   └── package.json             # Node.js dependencies
├── dump.rdb                     # Redis data file
└── README.md                    # This documentation file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 14+**
- **npm or yarn**
- **Git**

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd integrations_technical_assessment
```

2. **Backend Setup:**
```bash
cd backend
pip install fastapi uvicorn redis httpx requests python-multipart
```

3. **Frontend Setup:**
```bash
cd ../frontend
npm install
```

### Running the Application

1. **Start Backend Server:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend Server:**
```bash
cd frontend
npm start
```

3. **Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🔧 Configuration

### HubSpot OAuth Setup

1. **Create HubSpot App:**
   - Visit [HubSpot Developer Portal](https://developers.hubspot.com/)
   - Create a new app
   - Configure OAuth settings:
     - **Redirect URL**: `http://localhost:8000/integrations/hubspot/oauth2callback`
     - **Scopes**: `contacts oauth`

2. **Update Credentials:**
   Edit `backend/integrations/hubspot.py`:
   ```python
   CLIENT_ID = 'your_actual_hubspot_client_id'
   CLIENT_SECRET = 'your_actual_hubspot_client_secret'
   ```

### Environment Variables

```bash
# Optional: Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication Endpoints

#### HubSpot Integration

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| POST | `/integrations/hubspot/authorize` | Generate OAuth URL | `user_id`, `org_id` |
| GET | `/integrations/hubspot/oauth2callback` | OAuth callback | `code`, `state` |
| POST | `/integrations/hubspot/credentials` | Get stored credentials | `user_id`, `org_id` |
| POST | `/integrations/hubspot/load` | Load HubSpot data | `credentials` |

#### Notion Integration

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| POST | `/integrations/notion/authorize` | Generate OAuth URL | `user_id`, `org_id` |
| GET | `/integrations/notion/oauth2callback` | OAuth callback | `code`, `state` |
| POST | `/integrations/notion/credentials` | Get stored credentials | `user_id`, `org_id` |
| POST | `/integrations/notion/load` | Load Notion data | `credentials` |

#### Airtable Integration

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| POST | `/integrations/airtable/authorize` | Generate OAuth URL | `user_id`, `org_id` |
| GET | `/integrations/airtable/oauth2callback` | OAuth callback | `code`, `state` |
| POST | `/integrations/airtable/credentials` | Get stored credentials | `user_id`, `org_id` |
| POST | `/integrations/airtable/load` | Load Airtable data | `credentials` |

### Request/Response Examples

#### Authorize Request
```bash
curl -X POST "http://localhost:8000/integrations/hubspot/authorize" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=test_user&org_id=test_org"
```

**Response:**
```json
"https://app.hubspot.com/oauth/authorize?client_id=...&redirect_uri=...&scope=...&state=..."
```

#### Load Data Request
```bash
curl -X POST "http://localhost:8000/integrations/hubspot/load" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "credentials={\"access_token\":\"...\",\"refresh_token\":\"...\"}"
```

**Response:**
```json
[
  {
    "id": "123",
    "type": "Contact",
    "name": "John Doe",
    "creation_time": "2023-01-01T00:00:00Z",
    "last_modified_time": "2023-01-01T00:00:00Z",
    "url": "https://app.hubspot.com/contacts/123"
  }
]
```

## 🔐 OAuth Flow Implementation

### 1. Authorization Request
```python
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
```

### 2. OAuth Callback Handling
```python
async def oauth2callback_hubspot(request: Request):
    """Handle OAuth callback from HubSpot"""
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)
    
    # Verify state parameter
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')
    
    # Exchange code for access token
    response = await client.post(
        'https://api.hubapi.com/oauth/v1/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': code
        }
    )
    
    # Store credentials
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', 
                             json.dumps(response.json()), expire=600)
```

### 3. Data Retrieval
```python
async def get_items_hubspot(credentials):
    """Retrieve HubSpot contacts, companies, and deals"""
    access_token = credentials.get('access_token')
    
    # Get contacts
    contacts_response = requests.get(
        'https://api.hubapi.com/crm/v3/objects/contacts',
        headers={'Authorization': f'Bearer {access_token}'},
        params={'limit': 100}
    )
    
    # Get companies
    companies_response = requests.get(
        'https://api.hubapi.com/crm/v3/objects/companies',
        headers={'Authorization': f'Bearer {access_token}'},
        params={'limit': 50}
    )
    
    # Get deals
    deals_response = requests.get(
        'https://api.hubapi.com/crm/v3/objects/deals',
        headers={'Authorization': f'Bearer {access_token}'},
        params={'limit': 50}
    )
    
    return list_of_integration_item_metadata
```

## 📊 Data Models

### IntegrationItem
```python
class IntegrationItem:
    def __init__(
        self,
        id: Optional[str] = None,
        type: Optional[str] = None,
        directory: bool = False,
        parent_path_or_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        name: Optional[str] = None,
        creation_time: Optional[datetime] = None,
        last_modified_time: Optional[datetime] = None,
        url: Optional[str] = None,
        children: Optional[List[str]] = None,
        mime_type: Optional[str] = None,
        delta: Optional[str] = None,
        drive_id: Optional[str] = None,
        visibility: Optional[bool] = True,
    ):
```

### HubSpot Data Mapping

| HubSpot Object | IntegrationItem Fields |
|----------------|------------------------|
| Contact | `id`, `type="Contact"`, `name`, `creation_time`, `last_modified_time`, `url` |
| Company | `id`, `type="Company"`, `name`, `creation_time`, `last_modified_time`, `url` |
| Deal | `id`, `type="Deal"`, `name`, `creation_time`, `last_modified_time`, `url` |

## 🎨 Frontend Components

### HubSpot Integration Component
```javascript
export const HubSpotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            
            const response = await axios.post(
                `http://localhost:8000/integrations/hubspot/authorize`, 
                formData
            );
            
            const authURL = response?.data;
            const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=600');
            
            // Poll for window closure
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) { 
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    };

    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            
            const response = await axios.post(
                `http://localhost:8000/integrations/hubspot/credentials`, 
                formData
            );
            
            const credentials = response.data; 
            if (credentials) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({ 
                    ...prev, 
                    credentials: credentials, 
                    type: 'HubSpot' 
                }));
            }
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    };
};
```

### Integration Form
```javascript
const integrationMapping = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubSpotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    const [user, setUser] = useState('TestUser');
    const [org, setOrg] = useState('TestOrg');
    const [currType, setCurrType] = useState(null);
    const CurrIntegration = integrationMapping[currType];
    
    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column'>
            {/* User and Organization inputs */}
            {/* Integration type selection */}
            {/* Integration component */}
            {/* Data loading form */}
        </Box>
    );
};
```

## 🔄 Redis Configuration

### In-Memory Fallback System
```python
# In-memory storage for testing (fallback when Redis is not available)
_memory_storage: Dict[str, Any] = {}
_memory_expiry: Dict[str, float] = {}

try:
    redis_client = redis.Redis(host=redis_host, port=6379, db=0)
    asyncio.run(redis_client.ping())
    USE_REDIS = True
except Exception as e:
    print(f"Redis server not available, using in-memory storage: {e}")
    USE_REDIS = False

async def add_key_value_redis(key, value, expire=None):
    if USE_REDIS:
        await redis_client.set(key, value)
        if expire:
            await redis_client.expire(key, expire)
    else:
        _memory_storage[key] = value
        if expire:
            _memory_expiry[key] = time.time() + expire
```

## 🚨 Error Handling

### Backend Error Handling
```python
try:
    # API calls
    contacts_response = requests.get(
        'https://api.hubapi.com/crm/v3/objects/contacts',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if contacts_response.status_code != 200:
        raise HTTPException(status_code=contacts_response.status_code, 
                           detail='Failed to fetch contacts')
                           
except Exception as e:
    print(f"Error fetching HubSpot data: {e}")
    raise HTTPException(status_code=500, 
                       detail=f'Error fetching HubSpot data: {str(e)}')
```

### Frontend Error Handling
```javascript
try {
    const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/authorize`, 
        formData
    );
} catch (e) {
    setIsConnecting(false);
    if (e?.response?.data?.detail) {
        alert(e.response.data.detail);
    } else {
        alert('An unexpected error occurred');
    }
}
```

## 🧪 Testing

### Manual Testing Steps

1. **Start the Application:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

2. **Test HubSpot Integration:**
   - Open http://localhost:3000
   - Enter User ID and Organization ID
   - Select "HubSpot" from dropdown
   - Click "Connect to HubSpot"
   - Complete OAuth flow in popup window
   - Verify connection status shows "HubSpot Connected"
   - Click "Load Data" to retrieve HubSpot items
   - Check console for printed integration items

3. **Verify Data Loading:**
   - Contacts should be retrieved with names and IDs
   - Companies should be retrieved with names and IDs
   - Deals should be retrieved with names and IDs
   - All items should have proper URLs and timestamps

### API Testing

```bash
# Test backend health
curl http://localhost:8000/

# Test HubSpot authorization
curl -X POST "http://localhost:8000/integrations/hubspot/authorize" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=test_user&org_id=test_org"

# Test data loading (requires valid credentials)
curl -X POST "http://localhost:8000/integrations/hubspot/load" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "credentials={\"access_token\":\"test_token\"}"
```

## 🔒 Security Considerations

### OAuth Security
- **State Parameter**: Prevents CSRF attacks by validating state parameter
- **Token Storage**: Access tokens stored temporarily with expiration
- **HTTPS**: OAuth callbacks should use HTTPS in production
- **Scope Limitation**: Minimal required scopes for each integration

### API Security
- **Input Validation**: All inputs validated before processing
- **Error Handling**: Generic error messages prevent information leakage
- **CORS**: Configured for development environment
- **Rate Limiting**: Should be implemented in production

### Data Security
- **Token Encryption**: Consider encrypting stored tokens
- **Session Management**: Proper session handling with Redis
- **Access Control**: Implement user authentication in production

## 🚀 Deployment

### Production Checklist

1. **Environment Configuration:**
   ```bash
   # Production environment variables
   REDIS_HOST=your-redis-host
   REDIS_PORT=6379
   REDIS_PASSWORD=your-redis-password
   HUBSPOT_CLIENT_ID=your-hubspot-client-id
   HUBSPOT_CLIENT_SECRET=your-hubspot-client-secret
   ```

2. **Security Measures:**
   - Enable HTTPS
   - Configure proper CORS settings
   - Implement rate limiting
   - Add authentication middleware
   - Use environment variables for secrets

3. **Performance Optimization:**
   - Enable Redis clustering
   - Implement caching strategies
   - Add monitoring and logging
   - Configure load balancing

4. **Monitoring:**
   - Application performance monitoring
   - Error tracking and alerting
   - API usage analytics
   - Database performance monitoring

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues

1. **Module Import Error:**
   ```bash
   ERROR: Error loading ASGI app. Could not import module "main".
   ```
   **Solution:** Ensure you're running from the backend directory
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Redis Connection Error:**
   ```
   Redis server not available, using in-memory storage
   ```
   **Solution:** This is expected if Redis is not installed. The app will work with in-memory storage.

3. **Missing Dependencies:**
   ```bash
   ModuleNotFoundError: No module named 'fastapi'
   ```
   **Solution:** Install required packages
   ```bash
   pip install fastapi uvicorn redis httpx requests python-multipart
   ```

#### Frontend Issues

1. **CORS Errors:**
   ```
   Access to XMLHttpRequest at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
   ```
   **Solution:** Ensure backend is running and CORS is properly configured.

2. **OAuth Popup Issues:**
   - Check browser popup blockers
   - Verify redirect URLs in HubSpot app settings
   - Ensure proper state parameter handling

3. **API Connection Errors:**
   ```
   Network Error: Failed to fetch
   ```
   **Solution:** Check if backend server is running on correct port.

### Debug Commands

```bash
# Test backend import
python -c "import main; print('Backend import successful')"

# Test Redis client
python -c "import redis_client; print('Redis client configured')"

# Check API endpoints
curl http://localhost:8000/

# Test HubSpot integration
curl -X POST "http://localhost:8000/integrations/hubspot/authorize" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=test&org_id=test"
```

### Log Analysis

```bash
# Backend logs
tail -f backend.log

# Frontend logs (browser console)
# Check browser developer tools for errors

# Redis logs (if using Redis)
redis-cli monitor
```

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api)
- [Notion API Documentation](https://developers.notion.com/)
- [Airtable API Documentation](https://airtable.com/developers/web/api/introduction)

### OAuth Resources
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)

### Development Tools
- [Postman](https://www.postman.com/) - API testing
- [Redis Desktop Manager](https://redisdesktop.com/) - Redis management
- [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools) - React debugging

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests if applicable**
5. **Update documentation**
6. **Submit a pull request**

### Code Style

- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ESLint configuration
- **Comments**: Add docstrings for functions
- **Error Handling**: Comprehensive error handling
- **Logging**: Use appropriate log levels

## 📄 License

This project is part of the VectorShift Integrations Technical Assessment.

## 📞 Support

For questions or issues:
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

---

