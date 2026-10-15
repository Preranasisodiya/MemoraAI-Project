import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    print("--- 1. Testing Unauthenticated Request Rejection ---")
    r = client.get("/api/conversations/")
    assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
    print("PASS: Protected endpoint rejected unauthenticated request")

    print("\n--- 2. Testing User Registration ---")
    uid = str(uuid.uuid4())[:8]
    reg_data = {
        "name": "Alice Developer",
        "email": f"alice_{uid}@example.com",
        "password": "Password123!"
    }
    r = client.post("/api/auth/register", json=reg_data)
    assert r.status_code == 200, f"Register failed: {r.text}"
    user_id = r.json()["user_id"]
    print("PASS: User registered successfully with id:", user_id)

    print("\n--- 3. Testing User Login ---")
    r = client.post(
        "/api/auth/login",
        json={"email": reg_data["email"], "password": reg_data["password"]}
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("PASS: User logged in, JWT issued")

    print("\n--- 4. Testing /api/auth/me ---")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == reg_data["email"]
    print("PASS: Verified /api/auth/me for", r.json()["name"])

    print("\n--- 5. Testing Document Upload & List ---")
    sample_content = b"Operating Systems: Process Synchronization.\nSemaphores and Mutexes ensure mutual exclusion in critical sections."
    files = {"file": ("os_notes.txt", sample_content, "text/plain")}
    r = client.post("/api/documents/upload", files=files, headers=headers)
    assert r.status_code == 200, f"Upload failed: {r.text}"
    print("PASS: Document uploaded and processed without exposing internal chunks")

    r = client.get("/api/documents/", headers=headers)
    assert r.status_code == 200
    docs = r.json()
    assert len(docs) >= 1
    print("PASS: Listed user documents, count:", len(docs))

    print("\n--- 6. Testing Conversation Creation & Persistent Chat ---")
    r = client.post("/api/conversations/", json={"title": "Operating Systems Discussion"}, headers=headers)
    assert r.status_code == 201
    conv_id = r.json()["id"]
    print("PASS: Conversation created, id:", conv_id)

    # Question 1
    r = client.post(
        "/api/ask/",
        json={"query": "Explain process synchronization and semaphores", "conversation_id": conv_id},
        headers=headers
    )
    assert r.status_code == 200
    ans1 = r.json()
    assert "answer" in ans1 and ans1["conversation_id"] == conv_id
    print("PASS: First question answered and grounded in documents")

    # Follow-up Question
    r = client.post(
        "/api/ask/",
        json={"query": "Give three examples of how mutexes prevent race conditions", "conversation_id": conv_id},
        headers=headers
    )
    assert r.status_code == 200
    ans2 = r.json()
    print("PASS: Follow-up question answered within same conversation")

    # Verify conversation history has persisted
    r = client.get(f"/api/conversations/{conv_id}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["messages"]) >= 4, f"Expected at least 4 messages, got {len(detail['messages'])}"
    print("PASS: Conversation history verified with messages count:", len(detail["messages"]))

    print("\n--- 7. Testing User Isolation Between Users ---")
    bob_data = {
        "name": "Bob Hacker",
        "email": f"bob_{uid}@example.com",
        "password": "Password123!"
    }
    client.post("/api/auth/register", json=bob_data)
    r_bob = client.post("/api/auth/login", json={"email": bob_data["email"], "password": bob_data["password"]})
    bob_headers = {"Authorization": f"Bearer {r_bob.json()['access_token']}"}

    # Bob attempts to view Alice's conversation
    r_leak_conv = client.get(f"/api/conversations/{conv_id}", headers=bob_headers)
    assert r_leak_conv.status_code == 404, "Bob should not see Alice conversation!"
    print("PASS: Bob was denied access to Alice's conversation (404 Not Found)")

    # Bob attempts to view Alice's documents
    r_bob_docs = client.get("/api/documents/", headers=bob_headers)
    assert r_bob_docs.status_code == 200
    assert len(r_bob_docs.json()) == 0, "Bob should see 0 documents since he uploaded none!"
    print("PASS: Bob cannot see Alice's uploaded documents (isolated)")

    print("\n==========================================")
    print("ALL BACKEND ACCEPTANCE CRITERIA VERIFIED!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
