"""
database.py — NeoPept Pro
Configuration SQLAlchemy, modèles de données et fonctions d'accès à la base SQLite.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, desc
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ---------------------------------------------------------------------------
# Moteur & session
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///neopept.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Modèles ORM
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class ProteinRecord(Base):
    """Enregistrement d'une analyse de protéine dans la base de données."""

    __tablename__ = "protein_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom_proteine = Column(String(255), nullable=False, default="Sans nom")
    sequence = Column(String, nullable=False)
    poids_moleculaire = Column(Float, nullable=False)
    pi_score = Column(Float, nullable=False)
    date_analyse = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ProteinRecord id={self.id} nom='{self.nom_proteine}' "
            f"seq_len={len(self.sequence)} poids={self.poids_moleculaire:.2f}Da>"
        )


# ---------------------------------------------------------------------------
# Fonctions d'accès aux données (DAL)
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Crée toutes les tables si elles n'existent pas encore.

    À appeler une seule fois au démarrage de l'application (dans app.py).
    """
    Base.metadata.create_all(bind=engine)


def save_record(
    nom: str,
    sequence: str,
    poids_moleculaire: float,
    pi_score: float,
) -> ProteinRecord:
    """Persiste une nouvelle analyse de protéine dans la base de données.

    Args:
        nom: Nom donné au projet / à la protéine par l'utilisateur.
        sequence: Séquence d'acides aminés (lettres majuscules IUPAC).
        poids_moleculaire: Poids moléculaire calculé en Daltons.
        pi_score: Point isoélectrique calculé par Biopython.

    Returns:
        L'instance ``ProteinRecord`` fraîchement insérée (avec son id assigné).
    """
    db: Session = SessionLocal()
    try:
        record = ProteinRecord(
            nom_proteine=nom,
            sequence=sequence,
            poids_moleculaire=poids_moleculaire,
            pi_score=pi_score,
            date_analyse=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_all_records() -> List[ProteinRecord]:
    """Retourne toutes les analyses enregistrées, triées par date décroissante.

    Returns:
        Liste de ``ProteinRecord``, la plus récente en premier.
    """
    db: Session = SessionLocal()
    try:
        return (
            db.query(ProteinRecord)
            .order_by(desc(ProteinRecord.date_analyse))
            .all()
        )
    finally:
        db.close()


def get_record_by_id(record_id: int) -> Optional[ProteinRecord]:
    """Récupère un enregistrement précis par son identifiant.

    Args:
        record_id: Clé primaire de l'enregistrement recherché.

    Returns:
        L'instance ``ProteinRecord`` correspondante, ou ``None`` si introuvable.
    """
    db: Session = SessionLocal()
    try:
        return db.query(ProteinRecord).filter(ProteinRecord.id == record_id).first()
    finally:
        db.close()


def delete_record(record_id: int) -> bool:
    """Supprime un enregistrement de la base de données.

    Args:
        record_id: Clé primaire de l'enregistrement à supprimer.

    Returns:
        ``True`` si la suppression a eu lieu, ``False`` si l'id était introuvable.
    """
    db: Session = SessionLocal()
    try:
        record = db.query(ProteinRecord).filter(ProteinRecord.id == record_id).first()
        if record is None:
            return False
        db.delete(record)
        db.commit()
        return True
    finally:
        db.close()
