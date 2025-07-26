import os
import logging
import markdown
import json
import io
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, url_for, Response, flash, make_response
from app import app
from claude_service import ClaudeService, AVAILABLE_MODELS
from database import DatabaseManager
from models import SavedPrompt, CostTracking
from models_prompts import PRICING_DATA, calculate_cost, get_model_pricing
from app import db
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

# Initialiser les services
claude_service = ClaudeService()
db_manager = DatabaseManager()

# Authentification supprimée - accès direct

@app.route('/')
def index():
    """Page d'accueil - redirige vers dashboard"""
    return redirect(url_for('dashboard'))

# Routes d'authentification supprimées

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    try:
        stats = db_manager.get_stats()
        active_generations = db_manager.get_active_generations()
        recent_history = db_manager.get_history(limit=5)
        
        return render_template('dashboard.html', 
                             stats=stats,
                             active_generations=active_generations,
                             recent_history=recent_history,
                             claude_available=claude_service.anthropic_available,
                             openai_available=claude_service.openai_available)
    except Exception as e:
        logger.error(f"Erreur dashboard: {e}")
        flash('Erreur lors du chargement du dashboard.', 'error')
        return render_template('dashboard.html', 
                             stats={'total': 0, 'completed': 0, 'error': 0, 'generating': 0},
                             active_generations=[],
                             recent_history=[],
                             claude_available=False,
                             openai_available=False)

@app.route('/generator')

def generator():
    """Page de génération de contenu avec support de continuation"""
    try:
        # Vérifier si on est en mode continuation
        continue_id = request.args.get('continue')
        continue_data = None
        
        if continue_id:
            # Récupérer la génération à continuer
            generation = db_manager.get_generation_by_id(continue_id)
            if generation and generation.get('status') == 'completed':
                continue_data = {
                    'id': continue_id,
                    'original_prompt': generation.get('prompt', ''),
                    'original_response': generation.get('response', ''),
                    'model_used': generation.get('model_used', 'claude-sonnet-4-20250514')
                }
        
        return render_template('generator.html', 
                             claude_available=claude_service.anthropic_available,
                             openai_available=claude_service.openai_available,
                             available_models=AVAILABLE_MODELS,
                             continue_data=continue_data)
    except Exception as e:
        logger.error(f"Erreur page générateur: {e}")
        flash('Erreur lors du chargement du générateur.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/history')

def history():
    """Page de l'historique"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Pour simplifier, on récupère tout et on pagine côté client
        all_history = db_manager.get_history(limit=100)
        
        start = (page - 1) * per_page
        end = start + per_page
        history_page = all_history[start:end]
        
        total = len(all_history)
        has_prev = page > 1
        has_next = end < total
        
        return render_template('history.html',
                             history=history_page,
                             page=page,
                             per_page=per_page,
                             total=total,
                             has_prev=has_prev,
                             has_next=has_next)
    except Exception as e:
        logger.error(f"Erreur historique: {e}")
        flash('Erreur lors du chargement de l\'historique.', 'error')
        return render_template('history.html', history=[], page=1, per_page=20, total=0, has_prev=False, has_next=False)

@app.route('/api/generate', methods=['POST'])

def api_generate():
    """API pour lancer une génération avec support de continuation"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'Le prompt ne peut pas être vide'}), 400
        
        if len(prompt) > 50000:
            return jsonify({'error': 'Le prompt est trop long (maximum 50,000 caractères)'}), 400
        
        model = data.get('model', 'claude-sonnet-4-20250514')
        temperature = data.get('temperature', 1.0)
        
        # Vérifier si c'est une continuation
        continue_id = data.get('continue_from')
        conversation_history = []
        
        logger.info(f"[DEBUG] Continue ID reçu: {continue_id}")
        logger.info(f"[DEBUG] Data complète: {data}")
        
        if continue_id:
            # Récupérer la génération précédente pour construire l'historique
            original_generation = db_manager.get_generation_by_id(continue_id)
            if original_generation and original_generation.get('status') == 'completed':
                conversation_history = [
                    {"role": "user", "content": original_generation.get('prompt', '')},
                    {"role": "assistant", "content": original_generation.get('response', '')}
                ]
                logger.info(f"[CONTINUATION] Historique construit avec {len(conversation_history)} messages pour continue_id={continue_id}")
            else:
                logger.warning(f"[CONTINUATION] Génération non trouvée ou incomplète pour continue_id={continue_id}")
        
        logger.info(f"[API] Appel generate_text avec conversation_history: {len(conversation_history) if conversation_history else 0} messages")
        if conversation_history:
            logger.info(f"[API] Historique: {conversation_history}")
        result = claude_service.generate_text(prompt, model=model, stream=True, conversation_history=conversation_history)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur API génération: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/generation/<generation_id>/status')

def api_generation_status(generation_id):
    """API pour récupérer le statut d'une génération"""
    try:
        status = claude_service.get_generation_status(generation_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Génération non trouvée'}), 404
    except Exception as e:
        logger.error(f"Erreur API statut: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/generation/<generation_id>/stream')

def api_generation_stream(generation_id):
    """API pour streamer une génération en cours"""
    def generate_stream():
        try:
            last_chunk_index = 0
            max_iterations = 200  # Limite de sécurité réduite pour éviter timeouts
            iterations = 0
            
            import json
            import time
            
            while iterations < max_iterations:
                # Vérifier le statut avec retry pour la création
                status = claude_service.get_generation_status(generation_id)
                if not status and iterations < 50:  # Attendre 5 secondes max pour la création
                    time.sleep(0.1)
                    iterations += 1
                    continue
                elif not status:
                    yield f"data: {json.dumps({'error': 'Génération non trouvée'})}\n\n"
                    break
                
                # Récupérer les nouveaux chunks
                chunks = claude_service.get_stream_chunks(generation_id, last_chunk_index)
                
                for chunk in chunks:
                    yield f"data: {json.dumps({'content': chunk['content'], 'chunk_index': chunk['chunk_index']})}\n\n"
                    last_chunk_index = max(last_chunk_index, chunk['chunk_index'] + 1)
                
                # Envoyer le statut et progrès
                yield f"data: {json.dumps({'status': status['status'], 'progress': status.get('progress', 0), 'response': status.get('response', '')})}\n\n"
                
                # Si terminé, arrêter immédiatement
                if status['status'] in ['completed', 'error']:
                    logger.info(f"Stream terminé pour {generation_id}: {status['status']}")
                    break
                
                # Attendre avant la prochaine itération
                time.sleep(0.05)  # Délai réduit pour éviter les timeouts
                iterations += 1
            
            yield f"data: {json.dumps({'status': 'stream_ended'})}\n\n"
            
        except Exception as e:
            logger.error(f"Erreur stream: {e}")
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate_stream(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive'})

@app.route('/api/stats')

def api_stats():
    """API pour récupérer les statistiques"""
    try:
        stats = db_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erreur API stats: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/generation/<generation_id>')

def api_get_generation(generation_id):
    """API pour récupérer une génération complète"""
    try:
        generation = db_manager.get_generation_by_id(generation_id)
        if generation:
            return jsonify(generation)
        else:
            return jsonify({'error': 'Génération non trouvée'}), 404
    except Exception as e:
        logger.error(f"Erreur API récupération: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/generation/<generation_id>', methods=['DELETE'])

def api_delete_generation(generation_id):
    """API pour supprimer une génération"""
    try:
        success = db_manager.delete_generation(generation_id)
        if success:
            return jsonify({'message': 'Génération supprimée avec succès'})
        else:
            return jsonify({'error': 'Génération non trouvée'}), 404
    except Exception as e:
        logger.error(f"Erreur suppression génération: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/cleanup', methods=['POST'])

def api_cleanup():
    """API pour nettoyer les anciennes données"""
    try:
        data = request.get_json() if request.is_json else {}
        max_age_hours = data.get('max_age_hours', 24) if data else 24
        db_manager.cleanup_old_data(max_age_hours)
        return jsonify({'message': 'Nettoyage effectué avec succès'})
    except Exception as e:
        logger.error(f"Erreur nettoyage: {e}")
        return jsonify({'error': 'Erreur lors du nettoyage'}), 500

@app.route('/api/cleanup-stuck', methods=['POST'])

def api_cleanup_stuck():
    """API pour nettoyer les générations bloquées"""
    try:
        data = request.get_json() if request.is_json else {}
        max_age_minutes = data.get('max_age_minutes', 30) if data else 30
        count = db_manager.cleanup_stuck_generations(max_age_minutes)
        return jsonify({'message': f'{count} générations bloquées ont été nettoyées'})
    except Exception as e:
        logger.error(f"Erreur nettoyage générations bloquées: {e}")
        return jsonify({'error': 'Erreur lors du nettoyage'}), 500

@app.errorhandler(404)
def not_found(error):
    """Gestion des erreurs 404"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint non trouvé'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs 500"""
    logger.error(f"Erreur interne: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    return render_template('500.html'), 500

@app.route('/prompts')

def prompts():
    """Page de gestion des prompts"""
    return render_template('prompts.html')

# API Routes pour les prompts
@app.route('/api/prompts', methods=['GET'])

def api_get_prompts():
    """Récupérer tous les prompts"""
    try:
        prompts = SavedPrompt.query.order_by(SavedPrompt.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'prompts': [prompt.to_dict() for prompt in prompts]
        })
    except Exception as e:
        logger.error(f"Erreur récupération prompts: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts/<prompt_id>', methods=['GET'])

def api_get_prompt(prompt_id):
    """Récupérer un prompt spécifique"""
    try:
        prompt = SavedPrompt.query.get_or_404(prompt_id)
        return jsonify({
            'status': 'success',
            'prompt': prompt.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur récupération prompt: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts', methods=['POST'])

def api_create_prompt():
    """Créer un nouveau prompt"""
    try:
        import uuid
        data = request.get_json()
        
        prompt = SavedPrompt()
        prompt.id = str(uuid.uuid4())
        prompt.title = data['title']
        prompt.prompt_text = data['prompt_text']
        prompt.category = data.get('category', 'général')
        prompt.is_favorite = data.get('is_favorite', False)
        
        db.session.add(prompt)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'prompt': prompt.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur création prompt: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts/<prompt_id>', methods=['PUT'])

def api_update_prompt(prompt_id):
    """Mettre à jour un prompt"""
    try:
        prompt = SavedPrompt.query.get_or_404(prompt_id)
        data = request.get_json()
        
        prompt.title = data['title']
        prompt.prompt_text = data['prompt_text']
        prompt.category = data.get('category', 'général')
        prompt.is_favorite = data.get('is_favorite', False)
        prompt.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'prompt': prompt.to_dict()
        })
    except Exception as e:
        logger.error(f"Erreur mise à jour prompt: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts/<prompt_id>', methods=['DELETE'])

def api_delete_prompt(prompt_id):
    """Supprimer un prompt"""
    try:
        prompt = SavedPrompt.query.get_or_404(prompt_id)
        db.session.delete(prompt)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Erreur suppression prompt: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts/<prompt_id>/use', methods=['POST'])

def api_use_prompt(prompt_id):
    """Incrémenter le compteur d'utilisation d'un prompt"""
    try:
        prompt = SavedPrompt.query.get_or_404(prompt_id)
        prompt.usage_count += 1
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Erreur utilisation prompt: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prompts/<prompt_id>/favorite', methods=['POST'])

def api_toggle_favorite(prompt_id):
    """Basculer le statut favori d'un prompt"""
    try:
        prompt = SavedPrompt.query.get_or_404(prompt_id)
        data = request.get_json()
        prompt.is_favorite = data.get('is_favorite', False)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Erreur basculement favori: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/costs')

def costs():
    """Page de gestion des coûts"""
    return render_template('costs.html')

# API Routes pour les coûts
@app.route('/api/costs', methods=['GET'])

def api_get_costs():
    """Récupérer les données de coûts avec période"""
    try:
        period = request.args.get('period', '7d')
        
        # Calculer la date de début selon la période
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        else:  # 'all'
            start_date = datetime(2020, 1, 1)
        
        # Récupérer les données de coût
        costs_query = CostTracking.query.filter(CostTracking.created_at >= start_date)
        cost_records = costs_query.all()
        
        # Calculer le résumé
        total_cost = sum(record.total_cost for record in cost_records)
        month_start = now - timedelta(days=30)
        month_costs = [r for r in cost_records if r.created_at >= month_start]
        month_cost = sum(record.total_cost for record in month_costs)
        
        # Données par modèle
        model_costs = {}
        for record in cost_records:
            if record.model_id not in model_costs:
                model_costs[record.model_id] = {
                    'model_name': record.model_name,
                    'provider': record.provider,
                    'total_cost': 0.0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'count': 0
                }
            model_costs[record.model_id]['total_cost'] += record.total_cost
            model_costs[record.model_id]['input_tokens'] += record.input_tokens
            model_costs[record.model_id]['output_tokens'] += record.output_tokens
            model_costs[record.model_id]['count'] += 1
        
        # Convertir en liste et calculer pourcentages
        model_list = list(model_costs.values())
        max_cost = max((m['total_cost'] for m in model_list), default=1)
        for model in model_list:
            model['percentage'] = (model['total_cost'] / max_cost) * 100 if max_cost > 0 else 0
        
        # Données par fournisseur
        provider_costs = {}
        for record in cost_records:
            if record.provider not in provider_costs:
                provider_costs[record.provider] = 0.0
            provider_costs[record.provider] += record.total_cost
        
        provider_list = [{'provider': k, 'total_cost': v} for k, v in provider_costs.items()]
        
        # Timeline (par jour)
        timeline_data = {}
        for record in cost_records:
            date_key = record.created_at.strftime('%Y-%m-%d')
            if date_key not in timeline_data:
                timeline_data[date_key] = 0.0
            timeline_data[date_key] += record.total_cost
        
        # Trier par date
        sorted_timeline = sorted(timeline_data.items())
        timeline = {
            'labels': [item[0] for item in sorted_timeline],
            'costs': [item[1] for item in sorted_timeline]
        }
        
        # Table de tarification avec usage
        pricing_table = []
        for model_id, pricing in PRICING_DATA.items():
            usage_count = model_costs.get(model_id, {}).get('count', 0)
            total_cost = model_costs.get(model_id, {}).get('total_cost', 0.0)
            
            # Convertir les prix de $/1M tokens vers $/1K tokens pour l'affichage
            input_price_1k = pricing['input_cost'] / 1000  # De $/1M vers $/1K
            output_price_1k = pricing['output_cost'] / 1000  # De $/1M vers $/1K
            
            pricing_table.append({
                'model_id': model_id,
                'model_name': pricing['name'],
                'provider': pricing['provider'],
                'input_price': input_price_1k,
                'output_price': output_price_1k,
                'context_window': pricing['context_window'],
                'usage_count': usage_count,
                'total_cost': total_cost
            })
        
        # Générations les plus coûteuses
        expensive_query = costs_query.order_by(desc(CostTracking.total_cost)).limit(5)
        expensive_generations = []
        for record in expensive_query:
            # Récupérer le prompt associé
            generation = db_manager.get_generation_by_id(record.generation_id)
            prompt_preview = generation.get('prompt', '')[:100] if generation else ''
            
            expensive_generations.append({
                'generation_id': record.generation_id,
                'model_name': record.model_name,
                'provider': record.provider,
                'input_tokens': record.input_tokens,
                'output_tokens': record.output_tokens,
                'total_cost': record.total_cost,
                'created_at': record.created_at.isoformat(),
                'prompt_preview': prompt_preview
            })
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total_cost': total_cost,
                'month_cost': month_cost,
                'total_generations': len(cost_records)
            },
            'timeline': timeline,
            'by_model': model_list,
            'by_provider': provider_list,
            'pricing_table': pricing_table,
            'expensive_generations': expensive_generations
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération coûts: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/costs/export', methods=['GET'])

def api_export_costs():
    """Exporter les données de coûts en CSV"""
    try:
        period = request.args.get('period', '7d')
        
        # Même logique de période que ci-dessus
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        else:
            start_date = datetime(2020, 1, 1)
        
        costs_query = CostTracking.query.filter(CostTracking.created_at >= start_date)
        cost_records = costs_query.all()
        
        # Créer le CSV
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'Date', 'Modèle', 'Fournisseur', 'Input Tokens', 'Output Tokens',
            'Coût Input', 'Coût Output', 'Coût Total', 'ID Génération'
        ])
        
        # Données
        for record in cost_records:
            writer.writerow([
                record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                record.model_name,
                record.provider,
                record.input_tokens,
                record.output_tokens,
                f"${record.input_cost:.6f}",
                f"${record.output_cost:.6f}",
                f"${record.total_cost:.6f}",
                record.generation_id
            ])
        
        output.seek(0)
        
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=costs_{period}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur export coûts: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/playground/<generation_id>')

def playground(generation_id):
    """Page playground pour analyser une génération"""
    try:
        generation = db_manager.get_generation_by_id(generation_id)
        if not generation:
            flash('Génération non trouvée', 'error')
            return redirect(url_for('history'))
        
        # Convertir en format compatible avec le template
        created_at = generation.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.utcnow()
            
        generation_dict = {
            'id': generation.get('id'),
            'prompt': generation.get('prompt', ''),
            'response': generation.get('response', ''),
            'model_used': generation.get('model_used', 'Claude'),
            'created_at': created_at,
            'token_count': generation.get('token_count', 0),
            'status': generation.get('status', 'completed')
        }
        
        return render_template('playground.html', generation=generation_dict)
    
    except Exception as e:
        logger.error(f"Erreur page playground: {e}")
        flash('Erreur lors du chargement de la génération', 'error')
        return redirect(url_for('history'))

# ========== ROUTES DE PARTAGE ==========

@app.route('/api/share/<generation_id>', methods=['POST'])

def api_generate_share_token(generation_id):
    """Générer un token de partage pour une génération"""
    try:
        share_token = db_manager.generate_share_token(generation_id)
        if share_token:
            share_url = url_for('shared_generation', share_token=share_token, _external=True)
            return jsonify({
                'status': 'success',
                'share_token': share_token,
                'share_url': share_url
            })
        else:
            return jsonify({'status': 'error', 'message': 'Génération non trouvée'}), 404
    except Exception as e:
        logger.error(f"Erreur génération token partage: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/share/<share_token>')
def shared_generation(share_token):
    """Page publique pour afficher une génération partagée"""
    try:
        generation = db_manager.get_generation_by_share_token(share_token)
        if not generation:
            return render_template('error.html', 
                                 error_title="Génération non trouvée",
                                 error_message="Cette génération partagée n'existe pas ou a été supprimée."), 404
        
        # Traitement de la date
        created_at = generation.get('timestamp') or generation.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.utcnow()
        
        # Conversion du Markdown en HTML
        response_html = markdown.markdown(generation.get('response', ''), extensions=['codehilite', 'fenced_code'])
        
        generation_data = {
            'id': generation.get('id'),
            'prompt': generation.get('prompt', ''),
            'response': generation.get('response', ''),
            'response_html': response_html,
            'model_used': generation.get('model_used', 'Claude'),
            'created_at': created_at,
            'token_count': generation.get('token_count', 0),
            'status': generation.get('status', 'completed'),
            'share_token': share_token
        }
        
        return render_template('shared.html', generation=generation_data)
        
    except Exception as e:
        logger.error(f"Erreur affichage génération partagée: {e}")
        return render_template('error.html', 
                             error_title="Erreur",
                             error_message="Une erreur s'est produite lors du chargement de la génération."), 500

# ========== ROUTES D'EXPORTATION ==========

@app.route('/api/generation/<generation_id>/export/<format>')

def api_export_generation(generation_id, format):
    """Exporter une génération dans différents formats"""
    try:
        generation = db_manager.get_generation_by_id(generation_id)
        if not generation:
            return jsonify({'status': 'error', 'message': 'Génération non trouvée'}), 404
        
        # Traitement de la date
        created_at = generation.get('timestamp') or generation.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = created_at.strftime('%d/%m/%Y %H:%M')
            except:
                date_str = created_at
        elif created_at:
            date_str = created_at.strftime('%d/%m/%Y %H:%M') if hasattr(created_at, 'strftime') else str(created_at)
        else:
            date_str = 'Date inconnue'
        
        prompt = generation.get('prompt', '')
        content = generation.get('response', '')
        model_used = generation.get('model_used', 'Claude')
        token_count = generation.get('token_count', 0)
        filename = f"generation_{generation_id[:8]}"
        
        # Export TXT (texte brut)
        if format == 'txt':
            txt_content = f"""Génération AI Playground
========================

Modèle: {model_used}
Date: {date_str}
Tokens: {token_count}

PROMPT:
{prompt}

RÉPONSE:
{content}
"""
            response = make_response(txt_content)
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.txt"'
            return response
        
        # Export MD (Markdown avec métadonnées)
        elif format == 'md':
            md_content = f"""# Génération AI Playground

**Modèle:** {model_used}  
**Date:** {date_str}  
**Tokens:** {token_count}  
**ID:** {generation_id}

---

## Prompt

```
{prompt}
```

## Réponse

{content}

---

*Généré avec AI Playground - Plateforme d'analyse et manipulation de contenu IA*
"""
            response = make_response(md_content)
            response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.md"'
            return response
        
        # Export JSON (données structurées)
        elif format == 'json':
            json_data = {
                "metadata": {
                    "generation_id": generation_id,
                    "model_used": model_used,
                    "created_at": date_str,
                    "token_count": token_count,
                    "status": generation.get('status', 'completed'),
                    "exported_at": datetime.utcnow().isoformat(),
                    "exported_by": "AI Playground"
                },
                "content": {
                    "prompt": prompt,
                    "response": content
                },
                "technical": {
                    "response_length": len(content),
                    "prompt_length": len(prompt),
                    "estimated_reading_time": max(1, len(content.split()) // 200)  # mots par minute
                }
            }
            
            response = make_response(json.dumps(json_data, ensure_ascii=False, indent=2))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.json"'
            return response
        
        # Export HTML (page formatée)
        elif format == 'html':
            # Conversion du Markdown en HTML
            response_html = markdown.markdown(content, extensions=['codehilite', 'fenced_code', 'tables'])
            
            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Génération {generation_id[:8]} - AI Playground</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }}
        .header {{
            border-bottom: 3px solid #007bff;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 2rem;
            border-radius: 0.5rem;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0 0 1rem 0;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .meta-item {{
            background: white;
            padding: 0.5rem;
            border-radius: 0.25rem;
            border: 1px solid #dee2e6;
        }}
        .section {{
            margin: 2rem 0;
        }}
        .section h2 {{
            color: #495057;
            border-left: 4px solid #007bff;
            padding-left: 1rem;
        }}
        .prompt {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'Monaco', 'Consolas', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .response {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 1.5rem;
        }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 1rem;
            overflow-x: auto;
        }}
        code {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 0.2rem 0.4rem;
            font-size: 0.9em;
        }}
        pre code {{
            background: none;
            border: none;
            padding: 0;
        }}
        .footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
        }}
        @media print {{
            body {{ margin: 0; padding: 1rem; }}
            .header {{ background: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Génération AI Playground</h1>
        <div class="metadata">
            <div class="meta-item">
                <strong>Modèle:</strong><br>{model_used}
            </div>
            <div class="meta-item">
                <strong>Date:</strong><br>{date_str}
            </div>
            <div class="meta-item">
                <strong>Tokens:</strong><br>{token_count}
            </div>
            <div class="meta-item">
                <strong>ID:</strong><br>{generation_id[:8]}...
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📝 Prompt</h2>
        <div class="prompt">{prompt}</div>
    </div>

    <div class="section">
        <h2>🎯 Réponse</h2>
        <div class="response">
            {response_html}
        </div>
    </div>

    <div class="footer">
        <p>Généré avec <strong>AI Playground</strong> - Plateforme d'analyse et manipulation de contenu IA</p>
    </div>
</body>
</html>"""
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.html"'
            return response
        
        # Export PDF (via WeasyPrint ou xhtml2pdf en fallback)
        elif format == 'pdf':
            try:
                # Conversion du Markdown en HTML
                response_html = markdown.markdown(content, extensions=['codehilite', 'fenced_code', 'tables'])
                
                # Template HTML simplifié pour le PDF
                html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Génération {generation_id[:8]} - AI Playground</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: DejaVu Sans, Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .header {{
            border-bottom: 2pt solid #007bff;
            padding-bottom: 1em;
            margin-bottom: 2em;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 18pt;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 1em;
            margin-bottom: 2em;
            border: 1pt solid #dee2e6;
        }}
        .section {{
            margin: 1.5em 0;
            page-break-inside: avoid;
        }}
        .section h2 {{
            color: #495057;
            border-left: 4pt solid #007bff;
            padding-left: 1em;
            font-size: 14pt;
            margin-bottom: 1em;
        }}
        .prompt {{
            background-color: #f8f9fa;
            border: 1pt solid #dee2e6;
            padding: 1em;
            font-family: monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 1em;
        }}
        .response {{
            margin-bottom: 1em;
        }}
        pre {{
            background-color: #f8f9fa;
            border: 1pt solid #dee2e6;
            padding: 1em;
            overflow-wrap: break-word;
            white-space: pre-wrap;
            font-size: 10pt;
        }}
        code {{
            background-color: #f8f9fa;
            border: 1pt solid #dee2e6;
            padding: 0.2em 0.4em;
            font-size: 10pt;
        }}
        pre code {{
            background: none;
            border: none;
            padding: 0;
        }}
        p {{
            margin-bottom: 0.5em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Playground - Génération</h1>
    </div>

    <div class="metadata">
        <p><strong>Modèle:</strong> {model_used}</p>
        <p><strong>Date:</strong> {date_str}</p>
        <p><strong>Tokens:</strong> {token_count}</p>
        <p><strong>ID:</strong> {generation_id}</p>
    </div>

    <div class="section">
        <h2>Prompt</h2>
        <div class="prompt">{prompt}</div>
    </div>

    <div class="section">
        <h2>Réponse</h2>
        <div class="response">{response_html}</div>
    </div>
</body>
</html>"""
                
                # Essayer WeasyPrint d'abord
                try:
                    import weasyprint
                    pdf_bytes = weasyprint.HTML(string=html_template).write_pdf()
                    
                    response = make_response(pdf_bytes)
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    return response
                    
                except Exception as weasy_error:
                    logger.warning(f"WeasyPrint échoué: {weasy_error}, essai avec xhtml2pdf")
                    
                    # Fallback vers xhtml2pdf
                    try:
                        from xhtml2pdf import pisa
                        from io import BytesIO
                        
                        # Template simplifié pour xhtml2pdf
                        simple_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Génération AI Playground</title>
    <style>
        body {{ font-family: Arial; font-size: 12px; margin: 2cm; }}
        .header {{ border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .prompt {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
        pre {{ background: #f5f5f5; padding: 10px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Playground - Génération</h1>
        <p>Modèle: {model_used} | Date: {date_str} | Tokens: {token_count}</p>
    </div>
    <div class="section">
        <h2>Prompt</h2>
        <div class="prompt">{prompt}</div>
    </div>
    <div class="section">
        <h2>Réponse</h2>
        <div>{content.replace('<', '&lt;').replace('>', '&gt;')}</div>
    </div>
</body>
</html>"""
                        
                        pdf_buffer = BytesIO()
                        pisa_status = pisa.CreatePDF(simple_html, dest=pdf_buffer)
                        
                        if hasattr(pisa_status, 'err') and pisa_status.err:
                            raise Exception("Erreur xhtml2pdf")
                        
                        pdf_bytes = pdf_buffer.getvalue()
                        pdf_buffer.close()
                        
                        response = make_response(pdf_bytes)
                        response.headers['Content-Type'] = 'application/pdf'
                        response.headers['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
                        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                        response.headers['Pragma'] = 'no-cache'
                        response.headers['Expires'] = '0'
                        return response
                        
                    except Exception as xhtml_error:
                        logger.error(f"xhtml2pdf échoué aussi: {xhtml_error}")
                        # Fallback final vers HTML
                        return redirect(url_for('api_export_generation', generation_id=generation_id, format='html'))
                
            except ImportError:
                # Fallback vers HTML si aucune librairie PDF n'est disponible
                logger.warning("Aucune librairie PDF disponible, fallback vers HTML")
                return redirect(url_for('api_export_generation', generation_id=generation_id, format='html'))
            except Exception as e:
                logger.error(f"Erreur export PDF: {e}")
                return jsonify({
                    'status': 'error', 
                    'message': f'Export PDF temporairement indisponible. Utilisez le format HTML.'
                }), 500
        
        else:
            return jsonify({'status': 'error', 'message': f'Format "{format}" non supporté. Formats disponibles: txt, md, html, json, pdf'}), 400
        
    except Exception as e:
        logger.error(f"Erreur export génération: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =============================================================================
# GESTION DES CLÉS API
# =============================================================================

@app.route('/api-keys')

def api_keys():
    """Page de gestion des clés API"""
    try:
        # Vérifier les clés existantes et leur statut
        api_key_status = {
            'anthropic_key_configured': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'openai_key_configured': bool(os.environ.get('OPENAI_API_KEY')),
            'xai_key_configured': bool(os.environ.get('XAI_API_KEY')),
            'anthropic_key_valid': False,
            'openai_key_valid': False,
            'xai_key_valid': False,
            'anthropic_key_suffix': '',
            'openai_key_suffix': '',
            'xai_key_suffix': '',
        }
        
        # Obtenir les suffixes des clés (derniers 4 caractères)
        if api_key_status['anthropic_key_configured']:
            key = os.environ.get('ANTHROPIC_API_KEY')
            api_key_status['anthropic_key_suffix'] = key[-4:] if len(key) >= 4 else '****'
            
        if api_key_status['openai_key_configured']:
            key = os.environ.get('OPENAI_API_KEY')
            api_key_status['openai_key_suffix'] = key[-4:] if len(key) >= 4 else '****'
            
        if api_key_status['xai_key_configured']:
            key = os.environ.get('XAI_API_KEY')
            api_key_status['xai_key_suffix'] = key[-4:] if len(key) >= 4 else '****'
        
        # Compter les clés configurées
        configured_count = sum([
            api_key_status['anthropic_key_configured'],
            api_key_status['openai_key_configured'], 
            api_key_status['xai_key_configured']
        ])
        
        # Statistiques des coûts pour l'usage
        try:
            cost_stats = db_manager.get_cost_statistics()
        except:
            cost_stats = {'total_cost_month': 0}
        
        return render_template('api_keys.html', 
                             configured_keys_count=configured_count,
                             valid_keys_count=0,  # À déterminer via les tests
                             available_models_count=15,  # Total des modèles supportés
                             monthly_cost=cost_stats.get('total_cost_month', 0),
                             anthropic_usage_cost=0,
                             openai_usage_cost=0,
                             xai_usage_cost=0,
                             anthropic_quota_limit=100,
                             openai_quota_limit=100,
                             xai_quota_limit=100,
                             anthropic_usage_percent=0,
                             openai_usage_percent=0,
                             xai_usage_percent=0,
                             **api_key_status)
    except Exception as e:
        logger.error(f"Erreur page clés API: {e}")
        return render_template('api_keys.html', error="Erreur lors du chargement")

@app.route('/api/api-keys', methods=['POST'])

def api_save_key():
    """Sauvegarder une clé API"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        api_key = data.get('api_key', '').strip()
        
        if not provider or not api_key:
            return jsonify({'error': 'Provider et clé API requis'}), 400
        
        # Valider le format de la clé selon le provider
        if provider == 'anthropic' and not api_key.startswith('sk-ant-'):
            return jsonify({'error': 'Clé Anthropic invalide (doit commencer par sk-ant-)'}), 400
        elif provider == 'openai' and not api_key.startswith('sk-'):
            return jsonify({'error': 'Clé OpenAI invalide (doit commencer par sk-)'}), 400
        elif provider == 'xai' and not api_key.startswith('xai-'):
            return jsonify({'error': 'Clé xAI invalide (doit commencer par xai-)'}), 400
        
        # Sauvegarder dans les variables d'environnement
        env_key = f'{provider.upper()}_API_KEY'
        if provider == 'xai':
            env_key = 'XAI_API_KEY'
        
        os.environ[env_key] = api_key
        
        # Redémarrer les clients AI pour utiliser la nouvelle clé
        try:
            claude_service.restart_clients()
        except:
            pass
        
        return jsonify({'message': f'Clé {provider} sauvegardée avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde clé: {e}")
        return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500

@app.route('/api/api-keys/<provider>/test', methods=['POST'])

def api_test_key(provider):
    """Tester une clé API"""
    try:
        # Obtenir la clé selon le provider
        env_key = f'{provider.upper()}_API_KEY'
        if provider == 'xai':
            env_key = 'XAI_API_KEY'
        
        api_key = os.environ.get(env_key)
        if not api_key:
            return jsonify({'valid': False, 'error': 'Clé non configurée'})
        
        # Tester la clé avec une requête simple
        if provider == 'anthropic':
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test"}]
                )
                return jsonify({'valid': True, 'message': 'Clé Anthropic valide'})
            except Exception as e:
                error_msg = str(e)
                if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                    return jsonify({'valid': False, 'error': 'Clé invalide ou expirée'})
                return jsonify({'valid': False, 'error': 'Erreur de connexion'})
                
        elif provider == 'openai':
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test"}]
                )
                return jsonify({'valid': True, 'message': 'Clé OpenAI valide'})
            except Exception as e:
                error_msg = str(e)
                if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                    return jsonify({'valid': False, 'error': 'Clé invalide ou expirée'})
                return jsonify({'valid': False, 'error': 'Erreur de connexion'})
                
        elif provider == 'xai':
            try:
                from openai import OpenAI
                client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
                response = client.chat.completions.create(
                    model="grok-2-1212",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test"}]
                )
                return jsonify({'valid': True, 'message': 'Clé xAI valide'})
            except Exception as e:
                error_msg = str(e)
                if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                    return jsonify({'valid': False, 'error': 'Clé invalide ou expirée'})
                return jsonify({'valid': False, 'error': 'Erreur de connexion'})
        
        return jsonify({'valid': False, 'error': 'Provider non supporté'})
        
    except Exception as e:
        logger.error(f"Erreur test clé: {e}")
        return jsonify({'valid': False, 'error': 'Erreur lors du test'})

@app.route('/api/api-keys/<provider>', methods=['DELETE'])

def api_delete_key(provider):
    """Supprimer une clé API"""
    try:
        env_key = f'{provider.upper()}_API_KEY'
        if provider == 'xai':
            env_key = 'XAI_API_KEY'
        
        if env_key in os.environ:
            del os.environ[env_key]
        
        # Redémarrer les clients AI
        try:
            claude_service.restart_clients()
        except:
            pass
        
        return jsonify({'message': f'Clé {provider} supprimée avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur suppression clé: {e}")
        return jsonify({'error': 'Erreur lors de la suppression'}), 500
