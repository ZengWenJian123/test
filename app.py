from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "industrial_ai.db"

app = Flask(__name__)


@dataclass
class LocalLLMConfig:
    base_url: str = os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.environ.get("LOCAL_LLM_MODEL", "qwen2.5:7b")
    timeout: int = int(os.environ.get("LOCAL_LLM_TIMEOUT", "20"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                production_line TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );

            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_name TEXT NOT NULL UNIQUE,
                stock_qty INTEGER NOT NULL,
                reorder_level INTEGER NOT NULL,
                unit TEXT NOT NULL DEFAULT 'pcs',
                supplier TEXT NOT NULL
            );
            """
        )

        seed_if_empty(conn)


def seed_if_empty(conn: sqlite3.Connection) -> None:
    order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if order_count > 0:
        return

    conn.executemany(
        """
        INSERT INTO orders(customer, product, quantity, due_date, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("华东汽车", "电机控制器", 120, "2026-04-02", "high", "in_progress"),
            ("海蓝装备", "工业传感器", 300, "2026-04-10", "medium", "pending"),
            ("智造科技", "机器人关节模块", 60, "2026-04-01", "high", "pending"),
        ],
    )

    conn.executemany(
        """
        INSERT INTO schedule(order_id, production_line, start_date, end_date, progress)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "Line-A", "2026-03-26", "2026-03-31", 45),
            (2, "Line-B", "2026-04-01", "2026-04-08", 0),
            (3, "Line-C", "2026-03-27", "2026-03-30", 10),
        ],
    )

    conn.executemany(
        """
        INSERT INTO materials(material_name, stock_qty, reorder_level, unit, supplier)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("IGBT模块", 22, 30, "pcs", "上海功率电子"),
            ("霍尔传感器", 1200, 800, "pcs", "深圳敏测"),
            ("铝合金壳体", 150, 200, "pcs", "苏州精密制造"),
            ("轴承", 90, 120, "pcs", "宁波轴承厂"),
        ],
    )


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


def call_local_llm(prompt: str, context: dict[str, Any]) -> str:
    cfg = LocalLLMConfig()
    message = (
        "你是工业运营助手，请基于结构化数据给出可执行建议。\n"
        f"上下文数据: {context}\n"
        f"问题: {prompt}\n"
        "输出要求：1) 风险 2) 建议动作 3) 预计收益。"
    )

    payload = {"model": cfg.model, "prompt": message, "stream": False}

    try:
        import json
        from urllib import request as urlrequest

        req = urlrequest.Request(
            f"{cfg.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=cfg.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("response", "模型无返回。")
    except Exception as exc:
        return (
            "本地模型暂不可用，以下是规则引擎建议：\n"
            f"- 待处理高优先级订单: {context['high_priority_pending']} 个\n"
            f"- 低库存物料: {context['low_stock_count']} 项\n"
            "- 建议先锁定高优先级订单产线，并对低库存物料触发补货。\n"
            f"(异常信息: {exc})"
        )


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/overview")
def overview() -> Any:
    with get_conn() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY due_date ASC").fetchall()
        schedule = conn.execute(
            """
            SELECT s.*, o.product, o.customer
            FROM schedule s
            JOIN orders o ON s.order_id = o.id
            ORDER BY s.start_date ASC
            """
        ).fetchall()
        materials = conn.execute("SELECT * FROM materials ORDER BY material_name ASC").fetchall()

    return jsonify(
        {
            "orders": rows_to_dicts(orders),
            "schedule": rows_to_dicts(schedule),
            "materials": rows_to_dicts(materials),
        }
    )


@app.post("/api/ai/decision")
def ai_decision() -> Any:
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "请给出今日运营建议").strip()

    with get_conn() as conn:
        high_priority_pending = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE priority='high' AND status!='completed'"
        ).fetchone()[0]
        low_stock_count = conn.execute(
            "SELECT COUNT(*) FROM materials WHERE stock_qty < reorder_level"
        ).fetchone()[0]
        delayed_orders = conn.execute(
            "SELECT COUNT(*) FROM schedule WHERE progress < 50 AND start_date <= date('now')"
        ).fetchone()[0]

    context = {
        "high_priority_pending": high_priority_pending,
        "low_stock_count": low_stock_count,
        "delayed_orders": delayed_orders,
    }
    answer = call_local_llm(question, context)
    return jsonify({"question": question, "context": context, "answer": answer})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
else:
    init_db()
