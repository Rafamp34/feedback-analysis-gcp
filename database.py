# -*- coding: utf-8 -*-
"""
Base de datos SQLite para almacenar feedback histórico
"""
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from contextlib import contextmanager


class FeedbackDatabase:
    """Base de datos persistente para almacenar análisis de feedback"""
    
    def __init__(self, db_path: str = "feedback_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializar tablas de la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla principal de feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT UNIQUE NOT NULL,
                    tipo TEXT NOT NULL,
                    sentimiento TEXT NOT NULL,
                    score REAL NOT NULL,
                    magnitude REAL,
                    categoria TEXT,
                    texto_muestra TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Tabla de entidades detectadas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entidades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    relevancia REAL,
                    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id)
                )
            """)
            
            # Tabla de estadísticas agregadas (para optimizar consultas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estadisticas_diarias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT UNIQUE NOT NULL,
                    total_feedback INTEGER DEFAULT 0,
                    positivos INTEGER DEFAULT 0,
                    negativos INTEGER DEFAULT 0,
                    neutrales INTEGER DEFAULT 0,
                    score_promedio REAL DEFAULT 0,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Índices para mejorar rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
                ON feedback(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_sentimiento 
                ON feedback(sentimiento)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_categoria 
                ON feedback(categoria)
            """)
            
            print("✅ Base de datos inicializada correctamente")
    
    def add_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Añadir feedback a la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Datos principales
                feedback_id = feedback_data.get("id")
                tipo = feedback_data.get("tipo", "texto")
                sentimiento = feedback_data.get("sentimiento", "neutral")
                score = feedback_data.get("score", 0.0)
                magnitude = feedback_data.get("magnitude")
                categoria = feedback_data.get("categoria", "General")
                texto_muestra = feedback_data.get("texto", "")[:500]  # Máximo 500 chars
                timestamp = feedback_data.get("timestamp", datetime.now().isoformat())
                
                # Metadata adicional como JSON
                metadata = {
                    "confianza": feedback_data.get("confianza"),
                    "rostros": feedback_data.get("rostros"),
                    "objetos": feedback_data.get("objetos"),
                    "audio_confianza": feedback_data.get("audio_confianza")
                }
                metadata_json = json.dumps({k: v for k, v in metadata.items() if v is not None})
                
                # Insertar feedback
                cursor.execute("""
                    INSERT INTO feedback 
                    (feedback_id, tipo, sentimiento, score, magnitude, categoria, 
                     texto_muestra, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (feedback_id, tipo, sentimiento, score, magnitude, categoria,
                      texto_muestra, timestamp, metadata_json))
                
                # Insertar entidades si existen
                if "entidades" in feedback_data and feedback_data["entidades"]:
                    for entidad in feedback_data["entidades"]:
                        cursor.execute("""
                            INSERT INTO entidades (feedback_id, nombre, tipo, relevancia)
                            VALUES (?, ?, ?, ?)
                        """, (feedback_id, entidad.get("nombre"), 
                              entidad.get("tipo"), entidad.get("relevancia", 0)))
                
                # Actualizar estadísticas diarias
                self._update_daily_stats(cursor, timestamp, sentimiento, score)
                
                print(f"✅ Feedback {feedback_id} guardado en base de datos")
                return True
                
        except sqlite3.IntegrityError:
            print(f"⚠️ Feedback {feedback_id} ya existe en la base de datos")
            return False
        except Exception as e:
            print(f"❌ Error al guardar feedback: {str(e)}")
            return False
    
    def _update_daily_stats(self, cursor, timestamp: str, sentimiento: str, score: float):
        """Actualizar estadísticas diarias agregadas"""
        fecha = timestamp.split('T')[0]  # Obtener solo la fecha YYYY-MM-DD
        
        # Verificar si existe registro para esta fecha
        cursor.execute("""
            SELECT * FROM estadisticas_diarias WHERE fecha = ?
        """, (fecha,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar registro existente
            total = existing['total_feedback'] + 1
            positivos = existing['positivos'] + (1 if sentimiento == 'positivo' else 0)
            negativos = existing['negativos'] + (1 if sentimiento == 'negativo' else 0)
            neutrales = existing['neutrales'] + (1 if sentimiento == 'neutral' else 0)
            
            # Recalcular score promedio
            score_acumulado = existing['score_promedio'] * existing['total_feedback']
            nuevo_score_promedio = (score_acumulado + score) / total
            
            cursor.execute("""
                UPDATE estadisticas_diarias
                SET total_feedback = ?, positivos = ?, negativos = ?, neutrales = ?,
                    score_promedio = ?, last_updated = ?
                WHERE fecha = ?
            """, (total, positivos, negativos, neutrales, nuevo_score_promedio,
                  datetime.now().isoformat(), fecha))
        else:
            # Crear nuevo registro
            cursor.execute("""
                INSERT INTO estadisticas_diarias 
                (fecha, total_feedback, positivos, negativos, neutrales, 
                 score_promedio, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fecha, 1,
                  1 if sentimiento == 'positivo' else 0,
                  1 if sentimiento == 'negativo' else 0,
                  1 if sentimiento == 'neutral' else 0,
                  score, datetime.now().isoformat()))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de todo el histórico"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de feedback
            cursor.execute("SELECT COUNT(*) as total FROM feedback")
            total = cursor.fetchone()['total']
            
            if total == 0:
                return {
                    "total": 0,
                    "positivos": 0,
                    "negativos": 0,
                    "neutrales": 0,
                    "score_promedio": 0,
                    "porcentaje_positivos": 0,
                    "porcentaje_negativos": 0,
                    "porcentaje_neutrales": 0
                }
            
            # Contar por sentimiento
            cursor.execute("""
                SELECT sentimiento, COUNT(*) as count 
                FROM feedback 
                GROUP BY sentimiento
            """)
            
            sentimientos = {row['sentimiento']: row['count'] for row in cursor.fetchall()}
            positivos = sentimientos.get('positivo', 0)
            negativos = sentimientos.get('negativo', 0)
            neutrales = sentimientos.get('neutral', 0)
            
            # Score promedio
            cursor.execute("SELECT AVG(score) as avg_score FROM feedback")
            score_promedio = cursor.fetchone()['avg_score'] or 0
            
            return {
                "total": total,
                "positivos": positivos,
                "negativos": negativos,
                "neutrales": neutrales,
                "score_promedio": round(score_promedio, 2),
                "porcentaje_positivos": round((positivos / total * 100), 1),
                "porcentaje_negativos": round((negativos / total * 100), 1),
                "porcentaje_neutrales": round((neutrales / total * 100), 1)
            }
    
    def get_recent_feedback(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtener feedback reciente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT feedback_id, tipo, sentimiento, score, categoria, 
                       texto_muestra, timestamp
                FROM feedback
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row['feedback_id'],
                    "tipo": row['tipo'],
                    "sentimiento": row['sentimiento'],
                    "score": round(row['score'], 2),
                    "categoria": row['categoria'],
                    "texto": row['texto_muestra'][:100] if row['texto_muestra'] else "",
                    "timestamp": row['timestamp']
                })
            
            return results
    
    def get_categories(self) -> Dict[str, int]:
        """Obtener distribución de categorías"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT categoria, COUNT(*) as count
                FROM feedback
                WHERE categoria IS NOT NULL
                GROUP BY categoria
                ORDER BY count DESC
            """)
            
            return {row['categoria']: row['count'] for row in cursor.fetchall()}
    
    def get_stats_by_type(self) -> Dict[str, int]:
        """Obtener estadísticas por tipo de análisis"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tipo, COUNT(*) as count
                FROM feedback
                GROUP BY tipo
            """)
            
            return {row['tipo']: row['count'] for row in cursor.fetchall()}
    
    def get_daily_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Obtener tendencias de los últimos N días"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fecha, total_feedback, positivos, negativos, neutrales, 
                       score_promedio
                FROM estadisticas_diarias
                ORDER BY fecha DESC
                LIMIT ?
            """, (days,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "fecha": row['fecha'],
                    "total": row['total_feedback'],
                    "positivos": row['positivos'],
                    "negativos": row['negativos'],
                    "neutrales": row['neutrales'],
                    "score_promedio": round(row['score_promedio'], 2)
                })
            
            return list(reversed(results))  # Más antiguo primero
    
    def get_top_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener las entidades más mencionadas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT nombre, tipo, COUNT(*) as mentions, 
                       AVG(relevancia) as avg_relevancia
                FROM entidades
                GROUP BY nombre, tipo
                ORDER BY mentions DESC, avg_relevancia DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "nombre": row['nombre'],
                    "tipo": row['tipo'],
                    "menciones": row['mentions'],
                    "relevancia_promedio": round(row['avg_relevancia'], 2) if row['avg_relevancia'] else 0
                })
            
            return results
    
    def get_sentiment_by_category(self) -> Dict[str, Dict[str, int]]:
        """Obtener distribución de sentimientos por categoría"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT categoria, sentimiento, COUNT(*) as count
                FROM feedback
                WHERE categoria IS NOT NULL
                GROUP BY categoria, sentimiento
                ORDER BY categoria, sentimiento
            """)
            
            result = {}
            for row in cursor.fetchall():
                categoria = row['categoria']
                sentimiento = row['sentimiento']
                count = row['count']
                
                if categoria not in result:
                    result[categoria] = {'positivo': 0, 'negativo': 0, 'neutral': 0}
                
                result[categoria][sentimiento] = count
            
            return result
    
    def clear_old_data(self, days: int = 90):
        """Limpiar datos antiguos (más de X días)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Eliminar feedback antiguo
            cursor.execute("""
                DELETE FROM feedback
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            
            # Limpiar entidades huérfanas
            cursor.execute("""
                DELETE FROM entidades
                WHERE feedback_id NOT IN (SELECT feedback_id FROM feedback)
            """)
            
            print(f"🗑️ Eliminados {deleted} registros antiguos (>{days} días)")
            return deleted
    
    def export_to_json(self, filepath: str = "feedback_export.json"):
        """Exportar toda la base de datos a JSON"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
            
            data = []
            for row in cursor.fetchall():
                feedback_dict = dict(row)
                
                # Obtener entidades asociadas
                cursor.execute("""
                    SELECT nombre, tipo, relevancia 
                    FROM entidades 
                    WHERE feedback_id = ?
                """, (feedback_dict['feedback_id'],))
                
                feedback_dict['entidades'] = [dict(e) for e in cursor.fetchall()]
                data.append(feedback_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"📁 Datos exportados a {filepath}")
            return filepath


# Función helper para inicializar la base de datos
def get_database(db_path: str = "feedback_analytics.db") -> FeedbackDatabase:
    """Obtener instancia de la base de datos"""
    return FeedbackDatabase(db_path)


if __name__ == "__main__":
    # Prueba de la base de datos
    db = FeedbackDatabase("test_feedback.db")
    print("✅ Base de datos de prueba creada")
    
    # Obtener estadísticas (debería estar vacía)
    stats = db.get_statistics()
    print(f"📊 Estadísticas iniciales: {stats}")