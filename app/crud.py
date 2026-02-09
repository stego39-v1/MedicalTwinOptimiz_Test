# В файле crud.py удалите или закомментируйте следующие функции:

# Symptom CRUD (УДАЛИТЬ ЭТОТ БЛОК)
# def get_symptom(db: Session, symptom_id: int):
#     return db.query(models.Symptom).filter(models.Symptom.id == symptom_id).first()
# 
# def get_symptoms(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Symptom).offset(skip).limit(limit).all()
# 
# def get_symptoms_by_category(db: Session, category: str):
#     return db.query(models.Symptom).filter(models.Symptom.category_name == category).all()
# 
# def create_symptom(db: Session, symptom: schemas.SymptomCreate):
#     db_symptom = models.Symptom(**symptom.model_dump())
#     db.add(db_symptom)
#     db.commit()
#     db.refresh(db_symptom)
#     return db_symptom