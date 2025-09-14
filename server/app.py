import os
import json
from datetime import datetime, timedelta
from typing import List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


# App setup
app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///instance/app.sqlite3")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Models
class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(64), unique=True, nullable=False)

    # Core
    full_name = db.Column(db.String(100), nullable=False)
    furigana = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="在籍")

    # Onboarding
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    date_of_joining = db.Column(db.Date, nullable=True)
    previous_job_leaving_date = db.Column(db.Date, nullable=True)
    salary = db.Column(db.String(50), nullable=True)
    grade = db.Column(db.String(50), nullable=True)
    is_double_work = db.Column(db.Boolean, default=False)
    is_dependent = db.Column(db.Boolean, default=False)
    scheduled_department = db.Column(db.String(100), nullable=True)
    scheduled_working_hours = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    commute_method = db.Column(db.String(100), nullable=True)
    employment_type = db.Column(db.String(100), nullable=True)

    # Offboarding
    last_working_day = db.Column(db.Date, nullable=True)
    date_of_leaving = db.Column(db.Date, nullable=True)
    is_resignation_submitted = db.Column(db.Boolean, default=False)
    handover_status = db.Column(db.String(100), nullable=True)
    is_company_property_returned = db.Column(db.Boolean, default=False)
    is_severance_pay = db.Column(db.Boolean, default=False)

    # Transfer
    transfer_destination_department = db.Column(db.String(100), nullable=True)
    transfer_date = db.Column(db.Date, nullable=True)
    is_working_hours_changed = db.Column(db.Boolean, default=False)
    is_commute_method_changed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship("Task", backref="employee", lazy=True, cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), index=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    assignee = db.Column(db.String(100), nullable=True, default="人事")
    status = db.Column(db.String(20), nullable=False, default="未完了")  # 未完了/進行中/完了
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PushSubscription(db.Model):
    __tablename__ = "push_subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), index=True, nullable=True)
    endpoint = db.Column(db.String(500), nullable=False)
    keys_auth = db.Column(db.String(256), nullable=False)
    keys_p256dh = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db():
    with app.app_context():
        db.create_all()


# Utilities
def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    # Accept YYYY-MM-DD
    return datetime.strptime(date_str, "%Y-%m-%d")


def gen_employee_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"EMP{ts}"


def to_task_dict(t: Task):
    return {
        "id": t.id,
        "employee_id": t.employee_id,
        "name": t.name,
        "due_date": t.due_date.isoformat(),
        "assignee": t.assignee,
        "status": t.status,
    }


def to_employee_dict(e: Employee):
    return {
        "id": e.id,
        "employee_id": e.employee_id,
        "full_name": e.full_name,
        "furigana": e.furigana,
        "department": e.department,
        "status": e.status,
        "address": e.address,
        "phone_number": e.phone_number,
        "date_of_joining": e.date_of_joining.isoformat() if e.date_of_joining else None,
        "previous_job_leaving_date": e.previous_job_leaving_date.isoformat() if e.previous_job_leaving_date else None,
        "salary": e.salary,
        "grade": e.grade,
        "is_double_work": e.is_double_work,
        "is_dependent": e.is_dependent,
        "scheduled_department": e.scheduled_department,
        "scheduled_working_hours": e.scheduled_working_hours,
        "age": e.age,
        "commute_method": e.commute_method,
        "employment_type": e.employment_type,
        "last_working_day": e.last_working_day.isoformat() if e.last_working_day else None,
        "date_of_leaving": e.date_of_leaving.isoformat() if e.date_of_leaving else None,
        "is_resignation_submitted": e.is_resignation_submitted,
        "handover_status": e.handover_status,
        "is_company_property_returned": e.is_company_property_returned,
        "is_severance_pay": e.is_severance_pay,
        "transfer_destination_department": e.transfer_destination_department,
        "transfer_date": e.transfer_date.isoformat() if e.transfer_date else None,
        "is_working_hours_changed": e.is_working_hours_changed,
        "is_commute_method_changed": e.is_commute_method_changed,
        "created_at": e.created_at.isoformat(),
        "updated_at": e.updated_at.isoformat(),
    }


# Schedule generation
def add_tasks(employee_id: int, tasks: List[dict]):
    for t in tasks:
        task = Task(
            employee_id=employee_id,
            name=t["name"],
            due_date=t["due_date"],
            assignee=t.get("assignee", "人事"),
            status="未完了",
        )
        db.session.add(task)


def generate_onboarding_tasks(join_date: datetime) -> List[dict]:
    return [
        {"name": "雇用契約書の作成", "assignee": "人事", "due_date": join_date - timedelta(days=7)},
        {"name": "社会保険の手続き", "assignee": "人事", "due_date": join_date - timedelta(days=3)},
        {"name": "社内システムアカウント発行", "assignee": "情報システム", "due_date": join_date - timedelta(days=3)},
        {"name": "備品準備", "assignee": "総務", "due_date": join_date - timedelta(days=5)},
    ]


def generate_offboarding_tasks(leaving_date: datetime) -> List[dict]:
    return [
        {"name": "社会保険の資格喪失手続き", "assignee": "人事", "due_date": leaving_date - timedelta(days=2)},
        {"name": "離職票の発行", "assignee": "人事", "due_date": leaving_date - timedelta(days=1)},
        {"name": "貸与品の返却", "assignee": "総務", "due_date": leaving_date - timedelta(days=1)},
        {"name": "最終給与の計算", "assignee": "経理", "due_date": leaving_date - timedelta(days=1)},
    ]


def generate_transfer_tasks(transfer_date: datetime) -> List[dict]:
    return [
        {"name": "異動先の部署への引き継ぎ", "assignee": "所属部署", "due_date": transfer_date},
        {"name": "社内システム権限の変更", "assignee": "情報システム", "due_date": transfer_date + timedelta(days=1)},
        {"name": "名刺の再発行", "assignee": "総務", "due_date": transfer_date + timedelta(days=2)},
        {"name": "座席の移動", "assignee": "総務", "due_date": transfer_date},
    ]


# Routes
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/employees", methods=["GET"])
def list_employees():
    q = Employee.query.order_by(Employee.created_at.desc()).all()
    return jsonify([to_employee_dict(e) for e in q])


@app.route("/api/employees/<int:eid>", methods=["GET"])
def get_employee(eid):
    e = Employee.query.get_or_404(eid)
    return jsonify(to_employee_dict(e))


@app.route("/api/employees/<int:eid>/tasks", methods=["GET"])
def get_employee_tasks(eid):
    _ = Employee.query.get_or_404(eid)
    tasks = Task.query.filter_by(employee_id=eid).order_by(Task.due_date.asc()).all()
    return jsonify([to_task_dict(t) for t in tasks])


@app.route("/api/tasks/<int:tid>", methods=["PATCH"])
def update_task(tid):
    body = request.get_json(force=True)
    task = Task.query.get_or_404(tid)
    status = body.get("status")
    if status:
        task.status = status
    assignee = body.get("assignee")
    if assignee:
        task.assignee = assignee
    db.session.commit()
    return jsonify(to_task_dict(task))


@app.route("/api/employees/onboarding", methods=["POST"])
def onboarding():
    body = request.get_json(force=True)
    join_date = parse_date(body.get("date_of_joining"))
    if not join_date:
        return jsonify({"error": "date_of_joining is required YYYY-MM-DD"}), 400

    e = Employee(
        employee_id=gen_employee_id(),
        full_name=body.get("full_name"),
        furigana=body.get("furigana"),
        department=body.get("department") or body.get("scheduled_department"),
        status="在籍",
        address=body.get("address"),
        phone_number=body.get("phone_number"),
        date_of_joining=join_date.date(),
        previous_job_leaving_date=(parse_date(body.get("previous_job_leaving_date")).date() if body.get("previous_job_leaving_date") else None),
        salary=body.get("salary"),
        grade=body.get("grade"),
        is_double_work=bool(body.get("is_double_work")),
        is_dependent=bool(body.get("is_dependent")),
        scheduled_department=body.get("scheduled_department"),
        scheduled_working_hours=body.get("scheduled_working_hours"),
        age=body.get("age"),
        commute_method=body.get("commute_method"),
        employment_type=body.get("employment_type"),
    )
    db.session.add(e)
    db.session.flush()  # get id

    tasks = generate_onboarding_tasks(join_date)
    add_tasks(e.id, tasks)
    db.session.commit()

    return jsonify({"employee": to_employee_dict(e), "tasks": [to_task_dict(t) for t in Task.query.filter_by(employee_id=e.id).all()]})


@app.route("/api/employees/offboarding", methods=["POST"])
def offboarding():
    body = request.get_json(force=True)
    employee_id = body.get("employee_db_id")  # internal numeric id or employee_id

    e: Optional[Employee] = None
    if isinstance(employee_id, int):
        e = Employee.query.get(employee_id)
    if not e and body.get("employee_id"):
        e = Employee.query.filter_by(employee_id=body.get("employee_id")).first()
    if not e:
        return jsonify({"error": "employee not found"}), 404

    leaving_date = parse_date(body.get("date_of_leaving"))
    if not leaving_date:
        return jsonify({"error": "date_of_leaving is required YYYY-MM-DD"}), 400

    e.status = "退職"
    e.last_working_day = parse_date(body.get("last_working_day")).date() if body.get("last_working_day") else None
    e.date_of_leaving = leaving_date.date()
    e.is_resignation_submitted = bool(body.get("is_resignation_submitted"))
    e.handover_status = body.get("handover_status")
    e.is_company_property_returned = bool(body.get("is_company_property_returned"))
    e.is_severance_pay = bool(body.get("is_severance_pay"))
    db.session.flush()

    tasks = generate_offboarding_tasks(leaving_date)
    add_tasks(e.id, tasks)
    db.session.commit()
    return jsonify({"employee": to_employee_dict(e), "tasks": [to_task_dict(t) for t in Task.query.filter_by(employee_id=e.id).all()]})


@app.route("/api/employees/transfer", methods=["POST"])
def transfer():
    body = request.get_json(force=True)
    employee_id = body.get("employee_db_id")
    e: Optional[Employee] = None
    if isinstance(employee_id, int):
        e = Employee.query.get(employee_id)
    if not e and body.get("employee_id"):
        e = Employee.query.filter_by(employee_id=body.get("employee_id")).first()
    if not e:
        return jsonify({"error": "employee not found"}), 404

    transfer_date = parse_date(body.get("transfer_date"))
    if not transfer_date:
        return jsonify({"error": "transfer_date is required YYYY-MM-DD"}), 400

    e.department = body.get("transfer_destination_department") or e.department
    e.transfer_destination_department = body.get("transfer_destination_department")
    e.transfer_date = transfer_date.date()
    e.is_working_hours_changed = bool(body.get("is_working_hours_changed"))
    e.is_commute_method_changed = bool(body.get("is_commute_method_changed"))
    e.status = "異動"
    db.session.flush()

    tasks = generate_transfer_tasks(transfer_date)
    add_tasks(e.id, tasks)
    db.session.commit()
    return jsonify({"employee": to_employee_dict(e), "tasks": [to_task_dict(t) for t in Task.query.filter_by(employee_id=e.id).all()]})


# Web Push API
def get_vapid_keys():
    pub = os.environ.get("VAPID_PUBLIC_KEY")
    prv = os.environ.get("VAPID_PRIVATE_KEY")
    return pub, prv


@app.route("/api/webpush/public_key", methods=["GET"])
def webpush_public_key():
    pub, _ = get_vapid_keys()
    return jsonify({"publicKey": pub or ""})


@app.route("/api/subscriptions", methods=["POST"])
def save_subscription():
    body = request.get_json(force=True)
    employee_db_id = body.get("employee_db_id")
    sub = body.get("subscription") or {}
    endpoint = sub.get("endpoint")
    keys = sub.get("keys") or {}
    if not endpoint or not keys.get("auth") or not keys.get("p256dh"):
        return jsonify({"error": "invalid subscription"}), 400

    record = PushSubscription(
        employee_id=employee_db_id,
        endpoint=endpoint,
        keys_auth=keys.get("auth"),
        keys_p256dh=keys.get("p256dh"),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"ok": True, "id": record.id})


def try_send_webpush(subscription: PushSubscription, payload: dict) -> bool:
    pub, prv = get_vapid_keys()
    if not pub or not prv:
        # Not configured
        return False
    try:
        from pywebpush import webpush, WebPushException

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"auth": subscription.keys_auth, "p256dh": subscription.keys_p256dh},
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=prv,
            vapid_claims={"sub": "mailto:admin@example.com"},
        )
        return True
    except Exception:
        return False


@app.route("/api/notify/upcoming", methods=["POST"])
def notify_upcoming():
    body = request.get_json(silent=True) or {}
    hours = int(body.get("hours", 24))
    now = datetime.utcnow()
    horizon = now + timedelta(hours=hours)

    tasks = Task.query.filter(Task.status != "完了", Task.due_date <= horizon, Task.due_date >= now).all()

    # Build messages per employee
    notified = 0
    for t in tasks:
        subs = PushSubscription.query.filter(
            (PushSubscription.employee_id == t.employee_id) | (PushSubscription.employee_id.is_(None))
        ).all()
        if not subs:
            continue
        payload = {
            "title": "タスク期限が近づいています",
            "body": f"{t.name} — 期限: {t.due_date.strftime('%Y-%m-%d %H:%M')}",
            "data": {"taskId": t.id, "employeeId": t.employee_id},
        }
        for s in subs:
            if try_send_webpush(s, payload):
                notified += 1

    return jsonify({"tasks": len(tasks), "notifications_sent": notified})


if __name__ == "__main__":
    os.makedirs("instance", exist_ok=True)
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

