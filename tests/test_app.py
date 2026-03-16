import io

from app import app


def test_index_ok():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "文档格式转换" in response.get_data(as_text=True)


def test_convert_markdown_ok():
    client = app.test_client()
    data = {
        "target": "markdown",
        "file": (io.BytesIO("hello".encode("utf-8")), "demo.txt"),
    }
    response = client.post("/convert", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert response.data == b"hello"
