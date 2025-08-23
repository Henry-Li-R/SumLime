from db import db

def test():
    result = db.session.execute(
        db.text(
            "select current_user, session_user, current_setting('is_superuser', true) as is_superuser;"
        )
    )
    for row in result:
        print(dict(row._mapping))
