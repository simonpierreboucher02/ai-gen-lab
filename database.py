import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app import db
from models import Generation, StreamBuffer

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire de base de données pour le dashboard Claude AI"""
    
    @staticmethod
    def save_generation(generation_data: Dict[str, Any]) -> bool:
        """Sauvegarde une génération"""
        try:
            prompt_hash = hashlib.md5(generation_data['prompt'].encode()).hexdigest()
            
            # Chercher une génération existante
            generation = Generation.query.filter_by(id=generation_data['id']).first()
            
            if generation:
                # Mettre à jour l'existante
                generation.prompt = generation_data['prompt']
                generation.response = (generation_data.get('response', '')).strip()
                generation.status = generation_data['status']
                generation.timestamp = datetime.fromisoformat(generation_data['timestamp'].replace('Z', '+00:00')) if isinstance(generation_data['timestamp'], str) else generation_data['timestamp']
                generation.started_at = datetime.fromisoformat(generation_data['started_at'].replace('Z', '+00:00')) if generation_data.get('started_at') and isinstance(generation_data['started_at'], str) else generation_data.get('started_at')
                generation.completed_at = datetime.fromisoformat(generation_data['completed_at'].replace('Z', '+00:00')) if generation_data.get('completed_at') and isinstance(generation_data['completed_at'], str) else generation_data.get('completed_at')
                generation.token_count = generation_data.get('token_count', 0)
                generation.progress = generation_data.get('progress', 0.0)
                generation.txt_file = generation_data.get('txt_file')
                generation.md_file = generation_data.get('md_file')
                generation.error_message = generation_data.get('error_message')
                generation.prompt_hash = prompt_hash
                generation.model_used = generation_data.get('model_used', 'claude-sonnet-4-20250514')
            else:
                # Créer une nouvelle génération
                generation = Generation()
                generation.id = generation_data['id']
                generation.prompt = generation_data['prompt']
                generation.response = (generation_data.get('response', '')).strip()
                generation.status = generation_data['status']
                generation.timestamp = datetime.fromisoformat(generation_data['timestamp'].replace('Z', '+00:00')) if isinstance(generation_data['timestamp'], str) else generation_data['timestamp']
                generation.started_at = datetime.fromisoformat(generation_data['started_at'].replace('Z', '+00:00')) if generation_data.get('started_at') and isinstance(generation_data['started_at'], str) else generation_data.get('started_at')
                generation.completed_at = datetime.fromisoformat(generation_data['completed_at'].replace('Z', '+00:00')) if generation_data.get('completed_at') and isinstance(generation_data['completed_at'], str) else generation_data.get('completed_at')
                generation.token_count = generation_data.get('token_count', 0)
                generation.progress = generation_data.get('progress', 0.0)
                generation.txt_file = generation_data.get('txt_file')
                generation.md_file = generation_data.get('md_file')
                generation.error_message = generation_data.get('error_message')
                generation.prompt_hash = prompt_hash
                generation.model_used = generation_data.get('model_used', 'claude-sonnet-4-20250514')
                db.session.add(generation)
            
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde génération: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def save_stream_chunk(generation_id: str, chunk_index: int, content: str) -> bool:
        """Sauvegarde un chunk de stream"""
        try:
            chunk = StreamBuffer()
            chunk.generation_id = generation_id
            chunk.chunk_index = chunk_index
            chunk.content = content
            db.session.add(chunk)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde chunk: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_generation_by_id(generation_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une génération par ID"""
        from app import app
        try:
            with app.app_context():
                generation = Generation.query.filter_by(id=generation_id).first()
                if generation:
                    return {
                    'id': generation.id,
                    'prompt': generation.prompt,
                    'response': (generation.response or "").strip(),
                    'status': generation.status,
                    'timestamp': generation.timestamp.isoformat() if generation.timestamp else None,
                    'started_at': generation.started_at.isoformat() if generation.started_at else None,
                    'completed_at': generation.completed_at.isoformat() if generation.completed_at else None,
                    'token_count': generation.token_count,
                    'progress': generation.progress,
                    'txt_file': generation.txt_file,
                    'md_file': generation.md_file,
                    'error_message': generation.error_message,
                    'model_used': generation.model_used,
                    'share_token': generation.share_token
                }
                return None
        except Exception as e:
            logger.error(f"Erreur récupération génération: {e}")
            return None
    
    @staticmethod
    def generate_share_token(generation_id: str) -> Optional[str]:
        """Génère un token de partage unique pour une génération"""
        try:
            generation = Generation.query.filter_by(id=generation_id).first()
            if not generation:
                return None
            
            # Générer un token unique
            share_token = secrets.token_urlsafe(24)
            
            # Vérifier l'unicité
            while Generation.query.filter_by(share_token=share_token).first():
                share_token = secrets.token_urlsafe(24)
            
            generation.share_token = share_token
            db.session.commit()
            
            return share_token
        except Exception as e:
            logger.error(f"Erreur génération token partage: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_generation_by_share_token(share_token: str) -> Optional[Dict[str, Any]]:
        """Récupère une génération par son token de partage"""
        try:
            generation = Generation.query.filter_by(share_token=share_token).first()
            if generation:
                return {
                    'id': generation.id,
                    'prompt': generation.prompt,
                    'response': (generation.response or "").strip(),
                    'status': generation.status,
                    'timestamp': generation.timestamp.isoformat() if generation.timestamp else None,
                    'started_at': generation.started_at.isoformat() if generation.started_at else None,
                    'completed_at': generation.completed_at.isoformat() if generation.completed_at else None,
                    'token_count': generation.token_count,
                    'progress': generation.progress,
                    'txt_file': generation.txt_file,
                    'md_file': generation.md_file,
                    'error_message': generation.error_message,
                    'model_used': generation.model_used,
                    'share_token': generation.share_token
                }
            return None
        except Exception as e:
            logger.error(f"Erreur récupération génération par token: {e}")
            return None
    
    @staticmethod
    def get_active_generations() -> List[Dict[str, Any]]:
        """Récupère les générations en cours"""
        try:
            generations = Generation.query.filter_by(status='generating').order_by(Generation.timestamp.desc()).all()
            return [
                {
                    'id': g.id,
                    'prompt': g.prompt[:100] + '...' if len(g.prompt) > 100 else g.prompt,
                    'status': g.status,
                    'progress': g.progress,
                    'timestamp': g.timestamp.isoformat() if g.timestamp else None,
                    'started_at': g.started_at.isoformat() if g.started_at else None
                }
                for g in generations
            ]
        except Exception as e:
            logger.error(f"Erreur récupération générations actives: {e}")
            return []
    
    @staticmethod
    def get_history(limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'historique des générations"""
        from app import app
        try:
            with app.app_context():
                generations = Generation.query.filter(
                    Generation.status.in_(['completed', 'error'])
                ).order_by(Generation.timestamp.desc()).limit(limit).all()
                
                return [
                    {
                        'id': g.id,
                        'prompt': g.prompt[:100] + '...' if len(g.prompt) > 100 else g.prompt,
                        'response': ((g.response or "").strip()[:200] + '...') if len((g.response or "").strip()) > 200 else (g.response or "").strip(),
                        'status': g.status,
                        'timestamp': g.timestamp.isoformat() if g.timestamp else None,
                        'completed_at': g.completed_at.isoformat() if g.completed_at else None,
                        'token_count': g.token_count,
                        'error_message': g.error_message,
                        'model_used': g.model_used
                    }
                    for g in generations
                ]
        except Exception as e:
            logger.error(f"Erreur récupération historique: {e}")
            return []
    
    @staticmethod
    def get_stats() -> Dict[str, int]:
        """Récupère les statistiques"""
        from app import app
        try:
            with app.app_context():
                total = Generation.query.count()
                completed = Generation.query.filter_by(status='completed').count()
                error = Generation.query.filter_by(status='error').count()
                generating = Generation.query.filter_by(status='generating').count()
                
                return {
                    'total': total,
                    'completed': completed,
                    'error': error,
                    'generating': generating
                }
        except Exception as e:
            logger.error(f"Erreur récupération statistiques: {e}")
            return {'total': 0, 'completed': 0, 'error': 0, 'generating': 0}
    
    @staticmethod
    def get_generation(generation_id: str) -> Optional[Dict[str, Any]]:
        """Alias pour get_generation_by_id pour compatibilité"""
        return DatabaseManager.get_generation_by_id(generation_id)
    
    @staticmethod
    def get_stream_chunks(generation_id: str, start_index: int = 0) -> List[Dict[str, Any]]:
        """Récupère les chunks de stream d'une génération à partir d'un index"""
        from app import app
        try:
            with app.app_context():
                chunks = StreamBuffer.query.filter(
                    StreamBuffer.generation_id == generation_id,
                    StreamBuffer.chunk_index >= start_index
                ).order_by(StreamBuffer.chunk_index).all()
                
                return [
                    {
                        'chunk_index': chunk.chunk_index,
                        'content': chunk.content,
                        'timestamp': chunk.timestamp.isoformat() if chunk.timestamp else None
                    }
                    for chunk in chunks
                ]
        except Exception as e:
            logger.error(f"Erreur récupération chunks: {e}")
            return []
    
    @staticmethod
    def update_generation_progress(generation_id: str, progress: float):
        """Met à jour le progrès d'une génération"""
        try:
            generation = Generation.query.filter_by(id=generation_id).first()
            if generation:
                generation.progress = progress
                db.session.commit()
        except Exception as e:
            logger.error(f"Erreur mise à jour progrès: {e}")
            db.session.rollback()
    
    @staticmethod
    def complete_generation(generation_id: str, response: str, token_count: int):
        """Marque une génération comme terminée"""
        try:
            generation = Generation.query.filter_by(id=generation_id).first()
            if generation:
                generation.response = response.strip()
                generation.status = 'completed'
                generation.completed_at = datetime.utcnow()
                generation.token_count = token_count
                generation.progress = 1.0
                db.session.commit()
        except Exception as e:
            logger.error(f"Erreur completion génération: {e}")
            db.session.rollback()

    @staticmethod
    def delete_generation(generation_id: str) -> bool:
        """Supprime une génération et ses données associées"""
        from app import app
        try:
            with app.app_context():
                # Supprimer d'abord les données liées
                StreamBuffer.query.filter_by(generation_id=generation_id).delete()
                
                # Supprimer les coûts associés
                from models import CostTracking
                CostTracking.query.filter_by(generation_id=generation_id).delete()
                
                # Supprimer la génération
                generation = Generation.query.filter_by(id=generation_id).first()
                if generation:
                    db.session.delete(generation)
                    db.session.commit()
                    logger.info(f"Génération {generation_id} supprimée")
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Erreur suppression génération: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def cleanup_old_data(max_age_hours: int = 24):
        """Nettoie les anciennes données"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Nettoyer les chunks de stream anciens
            StreamBuffer.query.filter(StreamBuffer.timestamp < cutoff_time).delete()
            
            # Marquer les générations anciennes comme non-persistantes
            Generation.query.filter(
                Generation.timestamp < cutoff_time,
                Generation.status.in_(['completed', 'error'])
            ).update({'is_persistent': False})
            
            db.session.commit()
            logger.info(f"Nettoyage des données de plus de {max_age_hours}h effectué")
        except Exception as e:
            logger.error(f"Erreur nettoyage données: {e}")
            db.session.rollback()
    
    @staticmethod
    def cleanup_stuck_generations(max_age_minutes: int = 30):
        """Nettoie les générations bloquées en état 'generating' depuis trop longtemps"""
        from app import app
        try:
            with app.app_context():
                cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
                
                # Trouver les générations bloquées
                stuck_generations = Generation.query.filter(
                    Generation.status == 'generating',
                    Generation.created_at < cutoff_time
                ).all()
                
                count = 0
                for generation in stuck_generations:
                    generation.status = 'error'
                    generation.error_message = f'Génération interrompue automatiquement après {max_age_minutes} minutes'
                    generation.completed_at = datetime.utcnow()
                    count += 1
                
                db.session.commit()
                
                if count > 0:
                    logger.info(f"Nettoyé {count} générations bloquées")
                
                return count
                
        except Exception as e:
            logger.error(f"Erreur nettoyage générations bloquées: {e}")
            db.session.rollback()
            return 0
