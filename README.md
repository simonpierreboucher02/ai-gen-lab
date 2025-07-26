# AI Playground

## Overview

This is a Flask-based web application that provides a modern playground interface for analyzing and manipulating AI-generated content. The application features real-time streaming, persistent data storage, user authentication, responsive design, and advanced content analysis tools. It allows users to generate AI content, analyze generated text, extract code blocks, and manage their AI interactions through a clean, professional playground interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Database**: SQLite (default) with support for PostgreSQL via environment configuration
- **AI Integration**: Support multi-providers avec Claude et OpenAI selon spécifications exactes :
  - **Claude**: Sonnet 4.0 (64K), Opus 4.0 (32K), 3.7 Sonnet (128K) avec API bêta
  - **OpenAI**: GPT-4.1 (32K), GPT-4.1 Mini/Nano (32K), GPT-4o/Mini (16K) avec streaming temps réel
- **Authentication**: Supprimée - accès direct sans mot de passe
- **Logging**: Comprehensive logging system with file and console output

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 framework
- **Styling**: Custom CSS with CSS variables for theming support
- **JavaScript**: Vanilla JavaScript for dynamic interactions and real-time updates
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

## Key Components

### Core Application (`app.py`)
- Flask application factory pattern
- SQLAlchemy database configuration with connection pooling
- ProxyFix middleware for deployment behind reverse proxies
- Environment-based configuration management

### AI Service Layer (`claude_service.py`)
- Anthropic API client wrapper avec support multi-modèles
- 3 modèles Claude disponibles avec spécifications propres
- Gestion automatique des en-têtes bêta pour Claude 3.7 (128k-beta)
- Streaming text generation avec real-time updates
- Generation state management et progress tracking
- Error handling et fallback mechanisms

### Database Layer (`database.py`, `models.py`)
- **Generation Model**: Stores AI generation requests and responses
  - UUID-based primary keys
  - Prompt hashing for deduplication
  - Progress tracking and status management
  - File output storage paths
- **StreamBuffer Model**: Manages real-time streaming chunks
  - Sequential chunk ordering
  - Relationship to parent generation

### Web Interface (`routes.py`)
- **Authentication**: Supprimée pour accès direct
- **Dashboard**: Statistics and overview of generations
- **Generator**: Interface for creating new AI generations
- **History**: Browse and search previous generations
- **API Endpoints**: RESTful endpoints for AJAX interactions

### Frontend Assets
- **Templates**: Modular HTML templates with inheritance
- **CSS**: Modern styling with CSS custom properties
- **JavaScript**: Event handling, AJAX requests, and real-time updates

## Data Flow

1. **Direct Access**: Utilisateur accède directement au dashboard 
2. **Generation Request**: User submits prompt through web form
3. **AI Processing**: Claude service processes request with streaming
4. **Real-time Updates**: JavaScript polls for progress updates
5. **Data Persistence**: Generations and stream chunks saved to database
6. **File Output**: Generated content saved as text and markdown files

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and templating
- **SQLAlchemy**: Database ORM and migrations
- **Anthropic**: Claude AI API client

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library
- **Inter Font**: Modern typography

### Development Dependencies
- **Werkzeug**: WSGI utilities and development server
- **Python Logging**: Comprehensive logging system

## Deployment Strategy

### Development Setup
- SQLite database for local development
- Flask development server with debug mode
- File-based logging with rotation

### Production Considerations
- Environment variable configuration for:
  - `ANTHROPIC_API_KEY`: Claude API authentication
  - `DATABASE_URL`: Production database connection
  - `SESSION_SECRET`: Secure session management
- ProxyFix middleware configured for reverse proxy deployment
- Database connection pooling with health checks
- Structured logging for monitoring

### File Structure
```
/
├── app.py              # Flask application factory
├── main.py             # Application entry point
├── claude_service.py   # AI service integration
├── database.py         # Database operations
├── models.py           # SQLAlchemy models
├── routes.py           # Web routes and API endpoints
├── templates/          # Jinja2 HTML templates
├── static/            # CSS, JavaScript, and assets
└── attached_assets/   # Additional resources
```

## Recent Changes

### Janvier 2025 - Support Multi-Modèles Claude
- ✓ Ajout du choix entre 3 modèles Claude avec spécifications correctes
- ✓ Claude Sonnet 4.0 (claude-sonnet-4-20250514) : 64K tokens max (modèle par défaut)  
- ✓ Claude Opus 4.0 (claude-opus-4-20250514) : 32K tokens max (puissant pour créativité)
- ✓ Claude 3.7 Sonnet (claude-3-7-sonnet-20250219) : 128K tokens max avec API bêta
- ✓ Modèles OpenAI : GPT-4.1, GPT-4.1-Mini, GPT-4.1-Nano, GPT-4o, GPT-4o-Mini
- ✓ Format streaming chat.completions.create() pour OpenAI avec streaming temps réel
- ✓ Interface mise à jour avec sélection de modèle et paramètres de créativité
- ✓ Gestion automatique des en-têtes bêta pour les modèles qui l'exigent

### Janvier 2025 - Système de Prompts Sauvegardés
- ✓ Nouveau modèle SavedPrompt avec UUID, titre, contenu, catégorie, favoris, compteur d'utilisation
- ✓ Page /prompts avec interface complète de gestion (créer, éditer, supprimer, rechercher)
- ✓ API REST complète : GET, POST, PUT, DELETE sur /api/prompts avec endpoints spécialisés
- ✓ Fonctionnalités avancées : filtrage par catégorie, favoris, recherche textuelle
- ✓ Intégration générateur : bouton "Utiliser" transfère le prompt vers /generator avec pré-remplissage
- ✓ Statistiques en temps réel : total prompts, favoris, catégories
- ✓ Interface responsive avec cartes Bootstrap et animations CSS

### Janvier 2025 - Système d'URL Partageables
- ✓ Ajout du champ share_token dans le modèle Generation pour l'unicité des liens
- ✓ Nouvelles routes API /api/share/<generation_id> et /share/<share_token> 
- ✓ Page publique /share/<token> avec design moderne et rendu Markdown complet
- ✓ Template shared.html avec thème sombre/clair, métadonnées et coloration syntaxique
- ✓ Boutons de partage intégrés dans l'historique et le playground
- ✓ Fonctions JavaScript pour génération de liens et copie automatique dans le presse-papiers
- ✓ Modal de partage avec preview du lien et ouverture dans nouvel onglet
- ✓ Gestion d'erreurs complète et pages d'erreur personnalisées

### Janvier 2025 - Système d'Exportation Multi-Format
- ✓ Routes API complètes /api/generation/<id>/export/<format> pour tous les formats
- ✓ Export TXT : Texte brut avec métadonnées (modèle, date, tokens, prompt, réponse)
- ✓ Export MD : Markdown formaté avec structure claire et métadonnées
- ✓ Export HTML : Page web complète avec CSS intégré, responsive et prête à imprimer
- ✓ Export JSON : Données structurées avec métadonnées techniques et timestamps
- ✓ Export PDF : Génération via WeasyPrint avec mise en page professionnelle
- ✓ Boutons d'export intégrés dans le playground et sous-menus dans l'historique
- ✓ Fonction JavaScript exportGeneration() avec gestion d'erreurs et notifications
- ✓ CSS responsive pour les boutons d'export et sous-menus déroulants
- ✓ Gestion des fallbacks et messages d'erreur appropriés

### Janvier 2025 - Système de Suppression de Générations
- ✓ API DELETE /api/generation/<id> pour supprimer une génération complète
- ✓ Méthode delete_generation() dans DatabaseManager avec nettoyage complet
- ✓ Suppression en cascade : génération + streaming chunks + tracking coûts
- ✓ Fonction JavaScript deleteGeneration() avec confirmation utilisateur
- ✓ Animation de suppression CSS avec transitions fluides
- ✓ Bouton "Supprimer" ajouté dans le menu d'actions de l'historique
- ✓ Gestion d'erreurs complète et messages utilisateur appropriés

### Janvier 2025 - Interface de Gestion des Clés API
- ✓ Page /api-keys avec interface moderne et sécurisée pour gérer les clés
- ✓ Affichage masqué des clés (uniquement les 4 derniers caractères visibles)
- ✓ APIs REST complètes : POST /api/api-keys, DELETE /api/api-keys/<provider>, POST /api/api-keys/<provider>/test
- ✓ Validation automatique des formats de clés selon chaque provider
- ✓ Tests de clés en temps réel avec requêtes API authentiques
- ✓ Statistiques visuelles : clés configurées, valides, usage mensuel
- ✓ Redémarrage automatique des clients AI après modification des clés
- ✓ Interface responsive avec cartes provider et guides d'obtention des clés
- ✓ Mise à jour automatique des statuts de validation au chargement de la page

### Janvier 2025 - Suppression du Système d'Authentification
- ✓ Suppression complète du système de login/logout
- ✓ Accès direct au dashboard sans mot de passe
- ✓ Tous les décorateurs @require_auth supprimés
- ✓ Template login.html supprimé
- ✓ Routes d'authentification supprimées

### Janvier 2025 - Modèles OpenAI O-Series Authentiques (Raisonnement)
- ✓ Modèles O-Series authentiques : O3, O4-Mini, O1, O3-Mini utilisant la vraie API responses.create
- ✓ Parser SSE complet pour événements response.reasoning_summary_text.delta et response.output_text.delta
- ✓ Structure API exacte selon spécifications OpenAI : input_text, reasoning.effort, streaming SSE
- ✓ Support authentique de l'effort de raisonnement (low/medium/high) sans simulation
- ✓ Suppression complète du fallback GPT-4o pour garantir l'authenticité des modèles
- ✓ Formatage amélioré avec séparateur visuel (---) entre raisonnement et réponse finale
- ✓ Gestion d'erreurs directe sans simulation en cas d'indisponibilité API
- ✓ Tarification premium intégrée : O1 ($15/$60), O3 ($2/$8), O4-Mini/O3-Mini ($1.1/$4.4)
- ✓ Streaming temps réel authentique avec phases distinctes : réflexion → génération
- ✓ Integration complète dans le système de coûts et d'historique avec vraies métriques

The application is designed to be easily deployable on platforms like Replit, with minimal configuration required beyond setting the Anthropic API key.