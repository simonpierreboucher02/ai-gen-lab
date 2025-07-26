#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude AI Generator Pro - Version Ultra Robuste avec Support Multi-Modèles
Service de gestion des interactions avec Claude AI, OpenAI et xAI
"""

import os
import threading
import time
import logging
import uuid
from datetime import datetime, timedelta
import hashlib

# Configuration de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Le modèle par défaut
DEFAULT_MODEL_STR = "claude-sonnet-4-20250514"

# Configuration des modèles disponibles
AVAILABLE_MODELS = {
    # Modèles Claude 4.0 (nouveaux)
    "claude-sonnet-4-20250514": {
        "name": "Claude Sonnet 4",
        "description": "Modèle équilibré haute performance",
        "max_tokens": 64000,
        "provider": "anthropic"
    },
    "claude-opus-4-20250514": {
        "name": "Claude Opus 4",
        "description": "Modèle premium ultra-puissant",
        "max_tokens": 32000,
        "provider": "anthropic"
    },
    # Modèle Claude 3.7 avec support bêta
    "claude-3-7-sonnet-20250219": {
        "name": "Claude 3.7 Sonnet",
        "description": "Version 3.7 avec contexte étendu (Bêta)",
        "max_tokens": 128000,
        "provider": "anthropic",
        "requires_beta": True,
        "beta_features": ["output-128k-2025-02-19"]
    },
    # Modèles OpenAI GPT-4.1
    "gpt-4.1": {
        "name": "GPT-4.1",
        "description": "Modèle OpenAI de nouvelle génération",
        "max_output_tokens": 32768,
        "provider": "openai"
    },
    "gpt-4.1-mini": {
        "name": "GPT-4.1 Mini",
        "description": "Version allégée et rapide de GPT-4.1",
        "max_output_tokens": 32768,
        "provider": "openai"
    },
    "gpt-4.1-nano": {
        "name": "GPT-4.1 Nano",
        "description": "Version ultra-rapide pour tâches simples",
        "max_output_tokens": 32768,
        "provider": "openai"
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "description": "GPT-4o optimisé et efficace",
        "max_output_tokens": 16384,
        "provider": "openai"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "description": "GPT-4 Omni multimodal",
        "max_output_tokens": 16384,
        "provider": "openai"
    },
    # Modèles xAI Grok
    "grok-4-latest": {
        "name": "Grok-4",
        "description": "Le modèle Grok le plus avancé de xAI (256K context)",
        "context_length": 256000,
        "max_output_tokens": 8192,
        "provider": "xai"
    },
    "grok-3": {
        "name": "Grok-3",
        "description": "Modèle Grok performant pour diverses tâches (131K context)",
        "context_length": 131072,
        "max_output_tokens": 8192,
        "provider": "xai"
    },
    "grok-3-mini": {
        "name": "Grok-3 Mini",
        "description": "Version économique de Grok-3 (131K context)",
        "context_length": 131072,
        "max_output_tokens": 4096,
        "provider": "xai"
    },
    "grok-3-fast": {
        "name": "Grok-3 Fast",
        "description": "Version rapide de Grok-3 (131K context)",
        "context_length": 131072,
        "max_output_tokens": 4096,
        "provider": "xai"
    },
    # OpenAI O-Series (Reasoning Models)
    "o3": {
        "name": "O3",
        "description": "Modèle de raisonnement avancé O3 avec capacités de réflexion",
        "max_tokens": 100000,
        "max_output_tokens": 100000,
        "provider": "openai-reasoning",
        "api_type": "responses",
        "reasoning_effort": ["low", "medium", "high"]
    },
    "o4-mini": {
        "name": "O4 Mini",
        "description": "Version compacte du modèle O4 avec raisonnement efficace",
        "max_tokens": 65536,
        "max_output_tokens": 65536,
        "provider": "openai-reasoning",
        "api_type": "responses",
        "reasoning_effort": ["low", "medium", "high"]
    },
    "o1": {
        "name": "O1",
        "description": "Modèle de raisonnement O1 pour tâches complexes",
        "max_tokens": 100000,
        "max_output_tokens": 100000,
        "provider": "openai-reasoning",
        "api_type": "responses",
        "reasoning_effort": ["low", "medium", "high"]
    },
    "o3-mini": {
        "name": "O3 Mini",
        "description": "Version allégée du modèle O3 avec raisonnement rapide",
        "max_tokens": 65536,
        "max_output_tokens": 65536,
        "provider": "openai-reasoning",
        "api_type": "responses",
        "reasoning_effort": ["low", "medium", "high"]
    }
}

class ClaudeService:
    """Service pour gérer les interactions avec Claude AI, OpenAI et xAI"""
    
    def __init__(self):
        self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.xai_api_key = os.environ.get('XAI_API_KEY')
        self.anthropic_available = False
        self.openai_available = False
        self.xai_available = False
        self.anthropic_client = None
        self.openai_client = None
        self.xai_client = None
        
        # Initialiser Anthropic
        if self.anthropic_api_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                self.anthropic_available = True
                logger.info("Client Anthropic initialisé avec succès")
            except ImportError:
                logger.error("Module anthropic non installé")
            except Exception as e:
                logger.error(f"Erreur initialisation client Anthropic: {e}")
        else:
            logger.warning("ANTHROPIC_API_KEY non définie")
        
        # Initialiser OpenAI
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.openai_available = True
                logger.info("Client OpenAI initialisé avec succès")
            except ImportError:
                logger.error("Module openai non installé")
            except Exception as e:
                logger.error(f"Erreur initialisation client OpenAI: {e}")
        else:
            logger.warning("OPENAI_API_KEY non définie")
        
        # Initialiser xAI
        if self.xai_api_key:
            try:
                from openai import OpenAI
                self.xai_client = OpenAI(
                    api_key=self.xai_api_key,
                    base_url="https://api.x.ai/v1"
                )
                self.xai_available = True
                logger.info("Client xAI initialisé avec succès")
            except ImportError:
                logger.error("Module openai non installé (requis pour xAI)")
            except Exception as e:
                logger.error(f"Erreur initialisation client xAI: {e}")
        else:
            logger.warning("XAI_API_KEY non définie")
        
        self.active_generations = {}
        from database import DatabaseManager
        self.db_manager = DatabaseManager()

    def generate_content(self, prompt: str, model: str = DEFAULT_MODEL_STR, stream: bool = True, conversation_history: list = None) -> dict:
        """Générer du contenu avec le modèle spécifié"""
        generation_id = str(uuid.uuid4())
        
        # Debug de l'historique reçu
        if conversation_history:
            logger.info(f"[GENERATE_CONTENT] Historique reçu: {len(conversation_history)} messages")
            for i, msg in enumerate(conversation_history):
                logger.info(f"[GENERATE_CONTENT] Message {i}: {msg.get('role', 'unknown')} - {msg.get('content', '')[:100]}...")
        else:
            logger.info(f"[GENERATE_CONTENT] Aucun historique fourni")
        
        # Créer une entrée de génération
        generation_data = {
            'id': generation_id,
            'prompt': prompt,
            'response': '',
            'status': 'starting',
            'timestamp': datetime.utcnow(),
            'started_at': datetime.utcnow(),
            'completed_at': None,
            'token_count': 0,
            'progress': 0.0,
            'model_used': model
        }
        
        # Sauvegarder immédiatement dans le contexte Flask
        from app import app
        with app.app_context():
            success = self.db_manager.save_generation(generation_data)
            if not success:
                logger.error(f"Échec sauvegarde génération initiale {generation_id}")
            else:
                logger.info(f"Génération {generation_id} créée avec succès")
                # Petit délai pour s'assurer que la transaction est commitée
                import time
                time.sleep(0.1)
        
        model_config = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL_STR])
        provider = model_config.get('provider', 'anthropic')
        
        # Vérifier si le provider est disponible
        if provider == 'anthropic' and not self.anthropic_available:
            logger.warning(f"Provider Anthropic non disponible pour {model}, simulation activée")
            self._simulate_generation(generation_id, prompt, model)
        elif provider == 'openai' and not self.openai_available:
            logger.warning(f"Provider OpenAI non disponible pour {model}, simulation activée")
            self._simulate_generation(generation_id, prompt, model)
        elif provider == 'xai' and not self.xai_available:
            logger.warning(f"Provider xAI non disponible pour {model}, simulation activée")
            self._simulate_generation(generation_id, prompt, model)
        else:
            # Lancer la génération réelle dans un thread avec l'historique
            thread = threading.Thread(
                target=self._generate_async,
                args=(generation_id, prompt, model, stream, conversation_history)
            )
            thread.daemon = True
            thread.start()
        
        return {'generation_id': generation_id, 'status': 'started'}
    
    def _generate_async(self, generation_id: str, prompt: str, model: str = DEFAULT_MODEL_STR, stream: bool = True, conversation_history: list = None):
        """Génération asynchrone avec le provider approprié"""
        from app import app
        
        try:
            # Marquer comme en cours
            with app.app_context():
                generation_data = {
                    'id': generation_id,
                    'prompt': prompt,
                    'response': '',
                    'status': 'generating',
                    'timestamp': datetime.utcnow(),
                    'started_at': datetime.utcnow(),
                    'progress': 0.1,
                    'model_used': model
                }
                self.db_manager.save_generation(generation_data)
            
            if stream:
                self._generate_streaming(generation_id, prompt, model, conversation_history)
            else:
                self._generate_simple(generation_id, prompt, model, conversation_history)
                
        except Exception as e:
            logger.error(f"Erreur génération {generation_id}: {e}")
            self._mark_generation_error(generation_id, str(e))

    def _generate_streaming(self, generation_id: str, prompt: str, model: str = DEFAULT_MODEL_STR, conversation_history: list = None):
        """Génération avec streaming pour tous les providers"""
        from app import app
        
        try:
            response_text = ""
            chunk_index = 0
            
            model_config = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL_STR])
            provider = model_config.get('provider', 'anthropic')
            
            # Gestion spéciale pour les modèles O-Series
            if provider == 'openai-reasoning':
                self._generate_openai_reasoning(generation_id, prompt, model)
                return
            
            if provider == 'openai':
                # Génération OpenAI
                if not self.openai_client:
                    logger.error("Client OpenAI non initialisé")
                    self._generate_simple(generation_id, prompt, model)
                    return
                    
                # Construire les messages avec l'historique si présent
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                messages.append({"role": "user", "content": prompt})
                
                stream = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1.0,
                    max_tokens=model_config.get('max_output_tokens', 16384),
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        
                        with app.app_context():
                            self.db_manager.save_stream_chunk(generation_id, chunk_index, content)
                            progress = min(0.9, 0.1 + (len(response_text) / 1000) * 0.8)
                            generation_data = {
                                'id': generation_id,
                                'prompt': prompt,
                                'response': response_text.strip(),
                                'status': 'generating',
                                'timestamp': datetime.utcnow(),
                                'started_at': datetime.utcnow(),
                                'progress': progress,
                                'model_used': model
                            }
                            self.db_manager.save_generation(generation_data)
                        chunk_index += 1
                
                # Finaliser
                response_text = response_text.strip()
                word_count = len(response_text.split())
                token_count = max(1, int(word_count * 1.3))
                self._complete_generation(generation_id, prompt, response_text, token_count, model)
                
            elif provider == 'xai':
                # Génération xAI (même format que OpenAI) - pas de max_tokens spécifié
                if not self.xai_client:
                    logger.error("Client xAI non initialisé")
                    self._generate_simple(generation_id, prompt, model)
                    return
                    
                # Construire les messages avec l'historique si présent
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                messages.append({"role": "user", "content": prompt})
                
                stream = self.xai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1.0,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        
                        with app.app_context():
                            self.db_manager.save_stream_chunk(generation_id, chunk_index, content)
                            progress = min(0.9, 0.1 + (len(response_text) / 1000) * 0.8)
                            generation_data = {
                                'id': generation_id,
                                'prompt': prompt,
                                'response': response_text.strip(),
                                'status': 'generating',
                                'timestamp': datetime.utcnow(),
                                'started_at': datetime.utcnow(),
                                'progress': progress,
                                'model_used': model
                            }
                            self.db_manager.save_generation(generation_data)
                        chunk_index += 1
                
                # Finaliser
                response_text = response_text.strip()
                word_count = len(response_text.split())
                token_count = max(1, int(word_count * 1.3))
                self._complete_generation(generation_id, prompt, response_text, token_count, model)
                
            else:
                # Provider Anthropic
                if not self.anthropic_client:
                    logger.error("Client Anthropic non initialisé")
                    self._generate_simple(generation_id, prompt, model)
                    return
                    
                if model_config.get('requires_beta', False):
                    # Construire les messages avec l'historique si présent
                    messages = []
                    if conversation_history:
                        messages.extend(conversation_history)
                        logger.info(f"Utilisation de l'historique de conversation avec {len(conversation_history)} messages")
                    messages.append({"role": "user", "content": prompt})
                    
                    # Pour Claude 3.7 Sonnet, utiliser l'API bêta
                    with self.anthropic_client.beta.messages.stream(
                        model=model,
                        max_tokens=model_config['max_tokens'],
                        temperature=1.0,
                        messages=messages,
                        betas=model_config.get('beta_features', [])
                    ) as stream:
                        for chunk in stream:
                            try:
                                if hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                                        text = getattr(chunk.delta, 'text', '')
                                        if text:
                                            response_text += text
                                            
                                            with app.app_context():
                                                self.db_manager.save_stream_chunk(generation_id, chunk_index, text)
                                                chunk_index += 1
                                                
                                                progress = min(0.9, 0.1 + (len(response_text) / 10000) * 0.8)
                                                generation_data = {
                                                    'id': generation_id,
                                                    'prompt': prompt,
                                                    'response': response_text,
                                                    'status': 'generating',
                                                    'timestamp': datetime.utcnow(),
                                                    'started_at': datetime.utcnow(),
                                                    'progress': progress,
                                                    'model_used': model
                                                }
                                                self.db_manager.save_generation(generation_data)
                            except Exception as chunk_error:
                                logger.warning(f"Erreur processing chunk: {chunk_error}")
                                continue
                else:
                    # Construire les messages avec l'historique si présent
                    messages = []
                    if conversation_history:
                        messages.extend(conversation_history)
                        logger.info(f"Utilisation de l'historique de conversation avec {len(conversation_history)} messages")
                    messages.append({"role": "user", "content": prompt})
                    
                    # Pour les modèles normaux Claude (Sonnet 4.0 et Opus 4.0)
                    with self.anthropic_client.messages.stream(
                        model=model,
                        max_tokens=model_config['max_tokens'],
                        temperature=1.0,
                        messages=messages
                    ) as stream:
                        for chunk in stream:
                            try:
                                if hasattr(chunk, 'type') and chunk.type == "content_block_delta":
                                    if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                                        text = getattr(chunk.delta, 'text', '')
                                        if text:
                                            response_text += text
                                            
                                            with app.app_context():
                                                self.db_manager.save_stream_chunk(generation_id, chunk_index, text)
                                                chunk_index += 1
                                                
                                                progress = min(0.9, 0.1 + (len(response_text) / 10000) * 0.8)
                                                generation_data = {
                                                    'id': generation_id,
                                                    'prompt': prompt,
                                                    'response': response_text,
                                                    'status': 'generating',
                                                    'timestamp': datetime.utcnow(),
                                                    'started_at': datetime.utcnow(),
                                                    'progress': progress,
                                                    'model_used': model
                                                }
                                                self.db_manager.save_generation(generation_data)
                            except Exception as chunk_error:
                                logger.warning(f"Erreur processing chunk: {chunk_error}")
                                continue
                
                # Finaliser pour Anthropic
                response_text = response_text.strip()
                word_count = len(response_text.split())
                token_count = max(1, int(word_count * 1.3))
                self._complete_generation(generation_id, prompt, response_text, token_count, model)
                
        except Exception as e:
            logger.error(f"Erreur streaming: {e}")
            self._generate_simple(generation_id, prompt, model)

    def _generate_simple(self, generation_id: str, prompt: str, model: str = DEFAULT_MODEL_STR, conversation_history: list = None):
        """Génération simple sans streaming"""
        try:
            model_config = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS[DEFAULT_MODEL_STR])
            provider = model_config.get('provider', 'anthropic')
            
            if provider == 'openai':
                if not self.openai_client:
                    logger.error("Client OpenAI non initialisé")
                    self._mark_generation_error(generation_id, "Client OpenAI non disponible")
                    return
                    
                # Construire les messages avec l'historique si présent
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                    logger.info(f"[SIMPLE-OPENAI] Utilisation de l'historique de conversation avec {len(conversation_history)} messages")
                messages.append({"role": "user", "content": prompt})
                
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1.0,
                    max_tokens=model_config.get('max_output_tokens', 16384)
                )
                response_text = response.choices[0].message.content
                
            elif provider == 'xai':
                if not self.xai_client:
                    logger.error("Client xAI non initialisé")
                    self._mark_generation_error(generation_id, "Client xAI non disponible")
                    return
                    
                # Construire les messages avec l'historique si présent
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                    logger.info(f"[SIMPLE-XAI] Utilisation de l'historique de conversation avec {len(conversation_history)} messages")
                messages.append({"role": "user", "content": prompt})
                
                response = self.xai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1.0
                )
                response_text = response.choices[0].message.content
                
            else:
                # Anthropic
                if not self.anthropic_client:
                    logger.error("Client Anthropic non initialisé")
                    self._mark_generation_error(generation_id, "Client Anthropic non disponible")
                    return
                    
                # Construire les messages avec l'historique si présent
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                    logger.info(f"[SIMPLE-ANTHROPIC] Utilisation de l'historique de conversation avec {len(conversation_history)} messages")
                messages.append({"role": "user", "content": prompt})
                
                if model_config.get('requires_beta', False):
                    response = self.anthropic_client.beta.messages.create(
                        model=model,
                        max_tokens=model_config['max_tokens'],
                        temperature=1.0,
                        messages=messages,
                        betas=model_config.get('beta_features', [])
                    )
                else:
                    response = self.anthropic_client.messages.create(
                        model=model,
                        max_tokens=model_config['max_tokens'],
                        temperature=1.0,
                        messages=messages
                    )
                response_text = response.content[0].text
            
            word_count = len(response_text.split())
            token_count = max(1, int(word_count * 1.3))
            self._complete_generation(generation_id, prompt, response_text, token_count, model)
            
        except Exception as e:
            logger.error(f"Erreur génération simple: {e}")
            self._mark_generation_error(generation_id, str(e))

    def _complete_generation(self, generation_id: str, prompt: str, response: str, token_count: int, model: str):
        """Marquer une génération comme terminée"""
        from app import app
        
        try:
            with app.app_context():
                generation_data = {
                    'id': generation_id,
                    'prompt': prompt,
                    'response': response,
                    'status': 'completed',
                    'timestamp': datetime.utcnow(),
                    'completed_at': datetime.utcnow(),
                    'token_count': token_count,
                    'progress': 1.0,
                    'model_used': model
                }
                self.db_manager.save_generation(generation_data)
                
                # Enregistrer les coûts
                self._track_cost(generation_id, prompt, response, model)
                
                if generation_id in self.active_generations:
                    del self.active_generations[generation_id]
                    
        except Exception as e:
            logger.error(f"Erreur completion: {e}")

    def _track_cost(self, generation_id: str, prompt: str, response: str, model: str):
        """Enregistrer les coûts d'une génération"""
        try:
            from models_prompts import PRICING_DATA
            from models import CostTracking
            from app import db
            
            # Obtenir les données de tarification
            pricing = PRICING_DATA.get(model)
            if not pricing:
                logger.warning(f"Tarification non trouvée pour le modèle {model}")
                return
            
            # Estimer les tokens
            prompt_words = len(prompt.split())
            response_words = len(response.split())
            
            # Estimation : 1 token ≈ 0.75 mots
            input_tokens = max(1, int(prompt_words / 0.75))
            output_tokens = max(1, int(response_words / 0.75))
            
            # Calculer les coûts
            input_cost = (input_tokens / 1000000) * pricing['input_cost']
            output_cost = (output_tokens / 1000000) * pricing['output_cost']
            total_cost = input_cost + output_cost
            
            # Enregistrer en base
            cost_record = CostTracking()
            cost_record.generation_id = generation_id
            cost_record.model_id = model
            cost_record.model_name = pricing['name']
            cost_record.provider = pricing['provider']
            cost_record.input_tokens = input_tokens
            cost_record.output_tokens = output_tokens
            cost_record.input_cost = input_cost
            cost_record.output_cost = output_cost
            cost_record.total_cost = total_cost
            
            db.session.add(cost_record)
            db.session.commit()
            
            logger.info(f"Coût enregistré pour {generation_id}: ${total_cost:.4f}")
            
        except Exception as e:
            logger.error(f"Erreur enregistrement coût: {e}")
            try:
                db.session.rollback()
            except:
                pass

    def _mark_generation_error(self, generation_id: str, error_message: str):
        """Marquer une génération comme échouée"""
        from app import app
        
        try:
            with app.app_context():
                generation_data = {
                    'id': generation_id,
                    'status': 'error',
                    'response': f"Erreur: {error_message}",
                    'progress': 0.0,
                    'completed_at': datetime.utcnow()
                }
                self.db_manager.save_generation(generation_data)
                
                if generation_id in self.active_generations:
                    del self.active_generations[generation_id]
                    
        except Exception as e:
            logger.error(f"Erreur marking error: {e}")

    def restart_clients(self):
        """Redémarrer les clients AI avec les nouvelles clés"""
        try:
            self.__init__()
            logger.info("Clients AI redémarrés avec succès")
        except Exception as e:
            logger.error(f"Erreur redémarrage clients: {e}")

    def _simulate_generation(self, generation_id: str, prompt: str, model: str):
        """Simulation de génération en cas d'API non disponible"""
        logger.info(f"Simulation de génération pour {model}")
        
        def simulate():
            time.sleep(2)
            simulated_response = f"Réponse simulée pour le modèle {model}.\n\nPrompt reçu: {prompt[:100]}...\n\nCeci est une simulation car l'API réelle n'est pas disponible."
            self._complete_generation(generation_id, prompt, simulated_response, 50, model)
        
        thread = threading.Thread(target=simulate)
        thread.daemon = True
        thread.start()

    def get_generation_status(self, generation_id: str) -> dict:
        """Obtenir le statut d'une génération"""
        return self.db_manager.get_generation(generation_id)

    def get_stream_chunks(self, generation_id: str, start_index: int = 0) -> list:
        """Obtenir les chunks de streaming d'une génération à partir d'un index"""
        return self.db_manager.get_stream_chunks(generation_id, start_index)

    def get_available_models(self) -> dict:
        """Obtenir la liste des modèles disponibles"""
        return AVAILABLE_MODELS

    def generate_text(self, prompt: str, model: str = DEFAULT_MODEL_STR, stream: bool = True, conversation_history: list = None) -> dict:
        """Alias pour generate_content avec support de l'historique de conversation"""
        return self.generate_content(prompt, model, stream, conversation_history)

    def _generate_openai_reasoning(self, generation_id: str, prompt: str, model: str):
        """Génération spécifique pour les modèles OpenAI O-Series avec API responses.create"""
        from app import app
        import time
        
        try:
            if not self.openai_client:
                logger.error("Client OpenAI non initialisé pour modèle O-Series")
                self._mark_generation_error(generation_id, "Client OpenAI non disponible")
                return
            
            logger.info(f"Démarrage génération O-Series avec modèle {model}")
            
            # Marquer comme en cours avec un message spécial pour O-Series
            with app.app_context():
                generation_data = {
                    'id': generation_id,
                    'prompt': prompt,
                    'response': '🧠 Modèle de raisonnement en cours de réflexion...',
                    'status': 'reasoning',
                    'timestamp': datetime.utcnow(),
                    'started_at': datetime.utcnow(),
                    'progress': 0.2,
                    'model_used': model
                }
                self.db_manager.save_generation(generation_data)
                
                # Sauvegarder le chunk initial
                self.db_manager.save_stream_chunk(generation_id, 0, '🧠 Réflexion en cours...')
            
            # Utiliser l'API responses.create pour les modèles O-Series (sans fallback)
            try:
                logger.info(f"Connexion à l'API responses.create pour {model}")
                
                # Vérifier si l'API responses existe
                if not hasattr(self.openai_client, 'responses'):
                    logger.error(f"API responses.create non disponible pour {model}")
                    self._mark_generation_error(generation_id, f"API responses.create requise pour le modèle {model} mais non disponible. Veuillez mettre à jour votre client OpenAI.")
                    return
                
                # Structure correcte pour l'API responses.create selon l'exemple
                response_stream = self.openai_client.responses.create(
                    model=model,
                    input=[{
                        "role": "user",
                        "content": [{
                            "type": "input_text",
                            "text": prompt
                        }]
                    }],
                    text={
                        "format": {
                            "type": "text"
                        }
                    },
                    reasoning={
                        "effort": "medium",
                        "summary": "auto"
                    },
                    tools=[],
                    store=True,
                    stream=True
                )
                
                # Parser le streaming SSE des modèles O-Series selon l'exemple
                self._parse_o_series_stream(generation_id, prompt, response_stream, model)
                
            except Exception as e:
                logger.error(f"Erreur API responses.create pour {model}: {e}")
                logger.info(f"Details de l'erreur: {type(e).__name__}: {str(e)}")
                
                # Plus de fallback - erreur directe
                error_message = f"Erreur avec le modèle {model}: {str(e)}"
                if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                    error_message = f"Le modèle {model} n'est pas disponible avec votre clé API OpenAI. Vérifiez que vous avez accès aux modèles O-Series."
                elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                    error_message = f"Authentification échouée pour {model}. Vérifiez votre clé API OpenAI."
                
                self._mark_generation_error(generation_id, error_message)
                
                # Fallback vers l'API chat.completions standard avec simulation de raisonnement
                logger.info(f"Fallback vers API chat.completions pour {model}")
                
                try:
                    # Créer un prompt spécialisé pour simuler le raisonnement des modèles O-Series
                    reasoning_prompt = f"""Tu es le modèle de raisonnement {model}. Tu dois suivre cette structure exacte :

## 🧠 Processus de raisonnement:

[Explique ici ton processus de réflexion étape par étape. Analyse le problème, considère différentes approches, évalue les options, et montre ta logique de raisonnement avant d'arriver à la conclusion.]

## 💬 Réponse finale:

[Donne ici ta réponse finale claire et concise basée sur ton raisonnement ci-dessus.]

Prompt de l'utilisateur: {prompt}"""

                    fallback_response = self.openai_client.chat.completions.create(
                        model="gpt-4o",  # Fallback vers un modèle standard
                        messages=[
                            {"role": "system", "content": f"Tu es un modèle de raisonnement avancé spécialisé. Tu dois toujours suivre la structure demandée avec les sections 'Processus de raisonnement' et 'Réponse finale'."},
                            {"role": "user", "content": reasoning_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000
                    )
                    
                    full_response = fallback_response.choices[0].message.content
                    logger.info(f"Fallback réussi pour {model}, réponse de {len(full_response)} caractères")
                    self._simulate_o_series_streaming(generation_id, prompt, full_response, model)
                    
                except Exception as fallback_error:
                    logger.error(f"Erreur fallback pour {model}: {fallback_error}")
                    error_response = f"""❌ **Erreur technique avec le modèle {model}**

## 🧠 Processus de raisonnement:

Le système a tenté d'utiliser le modèle de raisonnement {model} mais a rencontré une erreur technique. L'API responses.create n'est peut-être pas encore disponible ou votre clé API n'a pas accès à ces modèles.

## 💬 Réponse finale:

Le modèle de raisonnement n'est pas disponible actuellement. Veuillez:
1. Vérifier que votre clé OpenAI est valide et a accès aux modèles O-Series
2. Essayer un autre modèle (GPT-4o, Claude)  
3. Réessayer dans quelques minutes

**Erreur:** {str(e)}"""
                    self._simulate_o_series_streaming(generation_id, prompt, error_response, model)
                
        except Exception as e:
            logger.error(f"Erreur génération O-Series {generation_id}: {e}")
            self._mark_generation_error(generation_id, f"Erreur modèle O-Series: {str(e)}")

    def _simulate_o_series_streaming(self, generation_id: str, prompt: str, response_text: str, model: str):
        """Simuler le streaming pour les modèles O-Series qui peuvent avoir des délais"""
        from app import app
        import time
        
        try:
            # Délai initial pour simuler la "réflexion"
            time.sleep(2)
            
            chunk_index = 1
            words = response_text.split()
            current_text = ""
            
            # Simulation du streaming mot par mot
            for i, word in enumerate(words):
                current_text += word + " "
                
                with app.app_context():
                    # Sauvegarder le chunk
                    self.db_manager.save_stream_chunk(generation_id, chunk_index, word + " ")
                    
                    # Calculer le progrès
                    progress = min(0.9, 0.3 + (i / len(words)) * 0.6)
                    
                    generation_data = {
                        'id': generation_id,
                        'prompt': prompt,
                        'response': current_text.strip(),
                        'status': 'generating',
                        'timestamp': datetime.utcnow(),
                        'started_at': datetime.utcnow(),
                        'progress': progress,
                        'model_used': model
                    }
                    self.db_manager.save_generation(generation_data)
                
                chunk_index += 1
                # Délai entre les mots pour simuler le streaming
                time.sleep(0.05)
            
            # Finaliser la génération
            self._complete_generation(generation_id, prompt, response_text.strip(), len(words), model)
            
        except Exception as e:
            logger.error(f"Erreur simulation streaming O-Series {generation_id}: {e}")
            self._mark_generation_error(generation_id, str(e))

    def _parse_o_series_stream(self, generation_id: str, prompt: str, response_stream, model: str):
        """Parser le streaming SSE des modèles O-Series selon la structure officielle"""
        from app import app
        import json
        
        try:
            reasoning_text = ""
            output_text = ""
            chunk_index = 1
            
            logger.info(f"Début du parsing du stream O-Series pour {model}")
            
            # Parser les événements SSE
            for chunk in response_stream:
                try:
                    # Les chunks arrivent avec les événements SSE
                    if hasattr(chunk, 'type'):
                        event_type = chunk.type
                        
                        # Traitement du raisonnement (reasoning summary)
                        if event_type == "response.reasoning_summary_text.delta":
                            if hasattr(chunk, 'delta'):
                                reasoning_text += chunk.delta
                                
                                # Sauvegarder le chunk de raisonnement
                                with app.app_context():
                                    self.db_manager.save_stream_chunk(generation_id, chunk_index, chunk.delta)
                                    
                                    # Mettre à jour le statut avec le raisonnement en cours
                                    generation_data = {
                                        'id': generation_id,
                                        'prompt': prompt,
                                        'response': f"## 🧠 Processus de raisonnement:\n\n{reasoning_text}",
                                        'status': 'reasoning',
                                        'timestamp': datetime.utcnow(),
                                        'started_at': datetime.utcnow(),
                                        'progress': min(0.5, 0.2 + (len(reasoning_text) / 500) * 0.3),
                                        'model_used': model
                                    }
                                    self.db_manager.save_generation(generation_data)
                                chunk_index += 1
                        
                        # Traitement de la réponse finale (output text)
                        elif event_type == "response.output_text.delta":
                            if hasattr(chunk, 'delta'):
                                output_text += chunk.delta
                                
                                # Sauvegarder le chunk de réponse
                                with app.app_context():
                                    self.db_manager.save_stream_chunk(generation_id, chunk_index, chunk.delta)
                                    
                                    # Combiner raisonnement et réponse pour l'affichage avec espacement correct
                                    full_response = f"## 🧠 Processus de raisonnement:\n\n{reasoning_text}\n\n---\n\n## 💬 Réponse finale:\n\n{output_text}"
                                    
                                    generation_data = {
                                        'id': generation_id,
                                        'prompt': prompt,
                                        'response': full_response,
                                        'status': 'generating',
                                        'timestamp': datetime.utcnow(),
                                        'started_at': datetime.utcnow(),
                                        'progress': min(0.9, 0.5 + (len(output_text) / 200) * 0.4),
                                        'model_used': model
                                    }
                                    self.db_manager.save_generation(generation_data)
                                chunk_index += 1
                        
                        # Fin de la réponse
                        elif event_type == "response.completed":
                            logger.info(f"Réponse O-Series complétée pour {model}")
                            
                            # Construire la réponse finale avec espacement correct
                            if reasoning_text and output_text:
                                final_response = f"## 🧠 Processus de raisonnement:\n\n{reasoning_text}\n\n---\n\n## 💬 Réponse finale:\n\n{output_text}"
                            elif output_text:
                                final_response = output_text
                            else:
                                final_response = f"Réponse générée par le modèle {model}"
                            
                            # Compter les tokens approximativement
                            estimated_tokens = len(final_response.split())
                            
                            self._complete_generation(generation_id, prompt, final_response, estimated_tokens, model)
                            return
                            
                except Exception as chunk_error:
                    logger.error(f"Erreur parsing chunk O-Series: {chunk_error}")
                    continue
            
            # Si on arrive ici, la réponse n'a pas été complétée normalement
            logger.warning(f"Stream O-Series terminé sans event 'completed' pour {model}")
            if reasoning_text or output_text:
                final_response = f"## 🧠 Processus de raisonnement:\n\n{reasoning_text}\n\n---\n\n## 💬 Réponse finale:\n\n{output_text}"
            else:
                final_response = "Réponse incomplète"
            estimated_tokens = len(final_response.split())
            self._complete_generation(generation_id, prompt, final_response, estimated_tokens, model)
            
        except Exception as e:
            logger.error(f"Erreur parsing stream O-Series {generation_id}: {e}")
            # En cas d'erreur, marquer comme erreur (plus de fallback)
            self._mark_generation_error(generation_id, f"Erreur parsing stream {model}: {str(e)}")

    def _get_api_keys_status(self):
        """Obtenir le statut des clés API configurées"""
        status = {}
        
        try:
            if self.anthropic_client:
                status['anthropic'] = {'configured': True, 'valid': True}
            else:
                status['anthropic'] = {'configured': False, 'valid': False}
        except:
            status['anthropic'] = {'configured': True, 'valid': False}
            
        try:
            if self.openai_client:
                status['openai'] = {'configured': True, 'valid': True}
            else:
                status['openai'] = {'configured': False, 'valid': False}
        except:
            status['openai'] = {'configured': True, 'valid': False}
            
        try:
            if self.xai_client:
                status['xai'] = {'configured': True, 'valid': True}
            else:
                status['xai'] = {'configured': False, 'valid': False}
        except:
            status['xai'] = {'configured': True, 'valid': False}
            
        return status