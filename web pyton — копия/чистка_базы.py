from data import db_session
from data.mems import Mem # Или Mem, смотря из какой таблицы удаляем

db_session.global_init("db/monday.db")
db_sess = db_session.create_session()

# Удаляем записи с id 1, 2, 3, 4
ids_to_delete = [1]
for obj_id in ids_to_delete:
    # Замените User на Mem, если удаляете мемы, а не пользователей
    item = db_sess.get(Mem, obj_id) 
    if item:
        db_sess.delete(item)

db_sess.commit()
print("Готово! Строки удалены.")
