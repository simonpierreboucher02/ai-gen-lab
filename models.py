from app import db
from datetime import datetime
import uuid

class Generation(db.Model):
    __tablename__ = 'generations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    token_count = db.Column(db.Integer, default=0)
    progress = db.Column(db.Float, default=0.0)
    txt_file = db.Column(db.String(255))
    md_file = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    prompt_hash = db.Column(db.String(32))
    model_used = db.Column(db.String(50), default='claude-sonnet-4-20250514')
    is_persistent = db.Column(db.Boolean, default=True)
    share_token = db.Column(db.String(32), unique=True, nullable=True)

class StreamBuffer(db.Model):
    __tablename__ = 'stream_buffer'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generation_id = db.Column(db.String(36), db.ForeignKey('generations.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    generation = db.relationship('Generation', backref='stream_chunks')


class SavedPrompt(db.Model):
    """Modèle pour les prompts sauvegardés"""
    __tablename__ = 'saved_prompts'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='général')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'prompt_text': self.prompt_text,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_favorite': self.is_favorite,
            'usage_count': self.usage_count
        }

class CostTracking(db.Model):
    __tablename__ = 'cost_tracking'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    generation_id = db.Column(db.String(36), db.ForeignKey('generations.id'), nullable=False)
    model_id = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    input_cost = db.Column(db.Float, default=0.0)
    output_cost = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'generation_id': self.generation_id,
            'model_id': self.model_id,
            'model_name': self.model_name,
            'provider': self.provider,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'input_cost': self.input_cost,
            'output_cost': self.output_cost,
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat()
        }
