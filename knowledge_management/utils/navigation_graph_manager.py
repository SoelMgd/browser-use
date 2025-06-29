"""
Gestionnaire pour les graphs de navigation stockés.

Ce module permet de :
1. Récupérer les graphs de navigation pour un site web
2. Analyser et formater les graphs pour l'injection dans les prompts
3. Identifier les patterns de navigation utiles
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class NavigationGraphManager:
    """Gestionnaire pour les graphs de navigation"""
    
    def __init__(self, graphs_dir: Optional[Path] = None):
        """
        Initialise le gestionnaire de graphs de navigation
        
        Args:
            graphs_dir: Répertoire contenant les graphs de navigation
        """
        if graphs_dir is None:
            graphs_dir = Path(__file__).parent.parent / "navigation_graphs"
        
        self.graphs_dir = graphs_dir
        self.graphs_dir.mkdir(exist_ok=True)
        
        logger.info(f"🗺️ Navigation Graph Manager initialisé: {self.graphs_dir}")
    
    def _extract_domain(self, url: str) -> str:
        """
        Extrait le domaine principal d'une URL
        
        Args:
            url: URL du site web
            
        Returns:
            Domaine principal (ex: 'admin_microsoft' pour 'admin.microsoft.com')
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Ignorer www
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Séparer par les points
            parts = domain.split('.')
            
            # Prendre tout sauf le TLD (dernière partie)
            if len(parts) > 1:
                # Tout sauf le dernier élément (TLD)
                domain_parts = parts[:-1]
                # Joindre avec des underscores
                return '_'.join(domain_parts)
            else:
                return domain
                
        except:
            # Fallback: essayer d'extraire manuellement
            url_lower = url.lower()
            if '://' in url_lower:
                url_lower = url_lower.split('://')[1]
            if '/' in url_lower:
                url_lower = url_lower.split('/')[0]
            
            # Ignorer www
            if url_lower.startswith('www.'):
                url_lower = url_lower[4:]
            
            # Séparer par les points
            parts = url_lower.split('.')
            if len(parts) > 1:
                domain_parts = parts[:-1]
                return '_'.join(domain_parts)
            else:
                return url_lower
    
    def _find_graph_file_by_domain(self, website_url: str) -> Optional[Path]:
        """
        Trouve le fichier de graph correspondant à une URL en cherchant le domaine dans le nom
        
        Args:
            website_url: URL du site web
            
        Returns:
            Chemin du fichier de graph trouvé ou None
        """
        try:
            target_domain = self._extract_domain(website_url)
            logger.info(f"🔍 Recherche de graph pour le domaine: {target_domain}")
            
            # Chercher dans tous les fichiers de graph
            for graph_file in self.graphs_dir.glob("*_graph.json"):
                filename = graph_file.stem  # Nom sans extension
                
                # Vérifier si le domaine cible est contenu dans le nom de fichier
                if target_domain in filename:
                    logger.info(f"✅ Graph trouvé: {graph_file.name}")
                    return graph_file
                
                # Vérifier aussi si le nom de fichier est contenu dans le domaine cible
                # (pour gérer les cas comme "airbnb" dans "subdomain_airbnb")
                if filename in target_domain:
                    logger.info(f"✅ Graph trouvé (correspondance inverse): {graph_file.name}")
                    return graph_file
            
            # Si pas trouvé, essayer une recherche plus flexible
            # Extraire le domaine principal (première partie)
            main_domain = target_domain.split('_')[0] if '_' in target_domain else target_domain
            
            for graph_file in self.graphs_dir.glob("*_graph.json"):
                filename = graph_file.stem
                
                # Vérifier si le domaine principal est dans le nom de fichier
                if main_domain in filename:
                    logger.info(f"✅ Graph trouvé (recherche flexible): {graph_file.name}")
                    return graph_file
            
            logger.info(f"❌ Aucun graph trouvé pour le domaine: {target_domain}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche de graph: {e}")
            return None
    
    def find_navigation_graphs_for_website(self, website_url: str, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        Trouve les graphs de navigation pour un site web donné
        
        Args:
            website_url: URL du site web
            max_age_days: Âge maximum des graphs à considérer (en jours)
            
        Returns:
            Liste des graphs de navigation avec leurs métadonnées
        """
        try:
            graphs = []
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Chercher le fichier correspondant à l'URL
            target_filepath = self._find_graph_file_by_domain(website_url)
            
            if target_filepath and target_filepath.exists():
                try:
                    # Vérifier l'âge du fichier
                    file_time = datetime.fromtimestamp(target_filepath.stat().st_mtime)
                    if file_time >= cutoff_date:
                        # Charger le contenu en texte brut
                        with open(target_filepath, 'r', encoding='utf-8') as f:
                            graph_content = f.read()
                        
                        # Extraire les métadonnées du nom de fichier
                        filename = target_filepath.stem
                        
                        graphs.append({
                            'file_path': str(target_filepath),
                            'graph_content': graph_content,  # Contenu brut
                            'file_time': file_time,
                            'website_url': website_url
                        })
                        logger.info(f"🔍 Graph de navigation trouvé pour {website_url}")
                    else:
                        logger.info(f"📅 Graph de navigation trouvé mais trop ancien pour {website_url}")
                except Exception as e:
                    logger.warning(f"❌ Erreur lors du chargement du graph {target_filepath}: {e}")
            else:
                logger.info(f"📭 Aucun graph de navigation trouvé pour {website_url}")
            
            return graphs
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche de graphs: {e}")
            return []
    
    def build_navigation_context(self, graphs: List[Dict[str, Any]], max_graphs: int = 3) -> str:
        """
        Construit un contexte de navigation à partir des graphs
        
        Args:
            graphs: Liste des graphs de navigation
            max_graphs: Nombre maximum de graphs à inclure
            
        Returns:
            Contexte formaté pour injection dans le prompt
        """
        if not graphs:
            return "No previous navigation patterns available for this website."
        
        # Limiter le nombre de graphs
        graphs = graphs[:max_graphs]
        
        context_parts = [
            "## Navigation graph of this website:\n"
        ]
        
        for i, graph_info in enumerate(graphs, 1):
            # Utiliser le contenu brut du graph
            graph_content = graph_info['graph_content']
            
            # Limiter la taille du contenu pour éviter des prompts trop longs
            if len(graph_content) > 10000:
                graph_content = graph_content[:10000] + "...\n[Content truncated for brevity]"
            
            # Ajouter le contenu du graph
            context_parts.append(graph_content)
        
        return "\n".join(context_parts)
    
    def save_navigation_graph(self, navigation_graph: dict, website_url: str) -> bool:
        """
        Sauvegarde un graph de navigation avec un nom basé sur le domaine
        
        Args:
            navigation_graph: Données du graph de navigation
            website_url: URL du site web
            
        Returns:
            True si la sauvegarde a réussi
        """
        try:
            # Extraire le domaine principal
            domain = self._extract_domain(website_url)
            
            # Créer le nom de fichier simple
            filename = f"{domain}_graph.json"
            filepath = self.graphs_dir / filename
            
            # Sauvegarder le graph (sans métadonnées)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(navigation_graph, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Graph de navigation sauvegardé : {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde du graph de navigation : {e}")
            return False
    