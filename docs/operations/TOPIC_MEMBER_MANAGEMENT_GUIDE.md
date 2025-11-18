# Topic Member Management Guide

## Overview
Admins can manage topic members, including viewing all users with their membership status and adding/removing members.

---

## API Endpoints

### 1. Get Users for Topic Addition
**GET** `/channels/topics/{topic_id}/users-for-addition`

**Purpose:** Get all users with a flag indicating if they're already members of the topic. Perfect for displaying a user selection UI where you can see who's already in the topic.

**Authentication:** Required (Bearer token)

**Authorization:** Admin only

**Query Parameters:**
- `search` (optional): Search by email or name

**Response:** `200 OK`
```json
[
  {
    "id": "user-uuid-1",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "avatar_url": "https://example.com/avatar1.jpg",
    "is_member": true
  },
  {
    "id": "user-uuid-2",
    "email": "jane.smith@example.com",
    "full_name": "Jane Smith",
    "avatar_url": "https://example.com/avatar2.jpg",
    "is_member": false
  },
  {
    "id": "user-uuid-3",
    "email": "bob.wilson@example.com",
    "full_name": "Bob Wilson",
    "avatar_url": null,
    "is_member": false
  }
]
```

**Features:**
- ✅ Returns all active users
- ✅ `is_member` flag indicates current membership status
- ✅ Supports search by email or name
- ✅ Sorted alphabetically by full name
- ✅ Admin-only access

**Error Responses:**
- `403 Forbidden` - User is not an admin
- `500 Internal Server Error` - Server error

---

### 2. Get Topic Members
**GET** `/channels/topics/{topic_id}/members`

**Purpose:** Get all current members of a topic (for @mentions).

**Authentication:** Required (Bearer token)

**Authorization:** Must be a member of the topic

**Response:** `200 OK`
```json
[
  {
    "id": "member-uuid",
    "user_id": "user-uuid",
    "user_email": "john@example.com",
    "user_full_name": "John Doe",
    "joined_at": "2025-11-14T10:00:00Z",
    "last_read_at": "2025-11-14T13:00:00Z",
    "is_active": true
  }
]
```

---

### 3. Add Member to Topic
**POST** `/channels/topics/{topic_id}/members/{user_id}`

**Purpose:** Add a user to the topic.

**Authentication:** Required (Bearer token)

**Authorization:** Admin only

**Response:** `201 Created`
```json
{
  "message": "Member added successfully"
}
```

**Real-time:** Emits `member_added` event via Socket.IO

---

### 4. Remove Member from Topic
**DELETE** `/channels/topics/{topic_id}/members/{user_id}`

**Purpose:** Remove a user from the topic (soft delete).

**Authentication:** Required (Bearer token)

**Authorization:** Admin only

**Response:** `204 No Content`

**Real-time:** Emits `member_removed` event via Socket.IO

---

## Frontend Integration

### User Selection UI for Adding Members

```jsx
import { useState, useEffect } from 'react';

const TopicMemberManager = ({ topicId }) => {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  // Fetch all users with membership status
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        
        const response = await fetch(
          `/channels/topics/${topicId}/users-for-addition?${params}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        
        const data = await response.json();
        setUsers(data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, [topicId, search]);

  const addMember = async (userId) => {
    try {
      const response = await fetch(
        `/channels/topics/${topicId}/members/${userId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        // Update local state
        setUsers(users.map(user => 
          user.id === userId 
            ? { ...user, is_member: true }
            : user
        ));
      }
    } catch (error) {
      console.error('Failed to add member:', error);
    }
  };

  const removeMember = async (userId) => {
    try {
      const response = await fetch(
        `/channels/topics/${topicId}/members/${userId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        // Update local state
        setUsers(users.map(user => 
          user.id === userId 
            ? { ...user, is_member: false }
            : user
        ));
      }
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  };

  return (
    <div className="topic-member-manager">
      <h2>Manage Topic Members</h2>
      
      {/* Search Input */}
      <input
        type="text"
        placeholder="Search users..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="search-input"
      />

      {/* User List */}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="user-list">
          {users.map(user => (
            <div key={user.id} className="user-item">
              <div className="user-info">
                {user.avatar_url && (
                  <img 
                    src={user.avatar_url} 
                    alt={user.full_name} 
                    className="avatar"
                  />
                )}
                <div>
                  <div className="user-name">{user.full_name}</div>
                  <div className="user-email">{user.email}</div>
                </div>
              </div>
              
              <div className="user-actions">
                {user.is_member ? (
                  <>
                    <span className="member-badge">Member</span>
                    <button 
                      onClick={() => removeMember(user.id)}
                      className="btn-remove"
                    >
                      Remove
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={() => addMember(user.id)}
                    className="btn-add"
                  >
                    Add to Topic
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TopicMemberManager;
```

---

## Styling Example (CSS)

```css
.topic-member-manager {
  padding: 20px;
}

.search-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: white;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name {
  font-weight: 600;
  color: #333;
}

.user-email {
  font-size: 0.9em;
  color: #666;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-badge {
  padding: 4px 12px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 500;
}

.btn-add {
  padding: 6px 16px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-add:hover {
  background: #45a049;
}

.btn-remove {
  padding: 6px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-remove:hover {
  background: #da190b;
}
```

---

## Testing the Endpoint

### Using cURL

**Get users for addition:**
```bash
curl -X GET "http://localhost:8000/channels/topics/{topic_id}/users-for-addition" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**With search:**
```bash
curl -X GET "http://localhost:8000/channels/topics/{topic_id}/users-for-addition?search=john" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Add member:**
```bash
curl -X POST "http://localhost:8000/channels/topics/{topic_id}/members/{user_id}" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Remove member:**
```bash
curl -X DELETE "http://localhost:8000/channels/topics/{topic_id}/members/{user_id}" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## Use Cases

### 1. Admin Panel - Manage Topic Members
Display all users with checkboxes or toggle buttons showing who's already a member.

### 2. Bulk Add Members
Select multiple non-members and add them all at once.

### 3. Search and Add
Search for specific users by name or email and add them to the topic.

### 4. Member Overview
See at a glance who is and isn't in the topic without making separate API calls.

---

## Summary

✅ **New endpoint:** `GET /channels/topics/{topic_id}/users-for-addition`  
✅ **Returns:** All users with `is_member` flag  
✅ **Admin only:** Restricted to admin users  
✅ **Search support:** Filter by email or name  
✅ **Sorted:** Alphabetically by full name  
✅ **Perfect for:** User selection UI in admin panels  

This makes it easy to build a member management interface where admins can see all users and quickly identify who's already in the topic versus who can be added!
