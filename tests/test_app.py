from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app


def test_index_ok():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "工业 AI 智能体决策平台" in response.get_data(as_text=True)


def test_overview_ok():
    client = app.test_client()
    response = client.get("/api/overview")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload and "orders" in payload
    assert len(payload["orders"]) >= 1


def test_ai_decision_ok():
    client = app.test_client()
    response = client.post("/api/ai/decision", json={"question": "今天排产怎么安排"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["question"] == "今天排产怎么安排"
    assert "answer" in payload
