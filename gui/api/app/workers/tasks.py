"""
Celery tasks for asynchronous job processing
"""
from app.workers.celery_app import celery_app
from app.services.layouts import compute_layout
from app.services.metrics import compute_centrality
from app.services.community import compute_community
from app.deps import get_artifacts_dir
import logging
import os
import json

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='run_layout')
def run_layout(self, graph_id: str, algorithm: str = "spring", seed: int = 42,
               dimensions: int = 2, iterations: int = 50):
    """Compute graph layout"""
    try:
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 10, 'phase': 'initializing'})
        
        # Compute layout
        self.update_state(state='PROGRESS', meta={'progress': 30, 'phase': 'computing layout'})
        positions = compute_layout(graph_id, algorithm, seed, dimensions, iterations)
        
        # Save results
        self.update_state(state='PROGRESS', meta={'progress': 80, 'phase': 'saving results'})
        artifacts_dir = get_artifacts_dir()
        job_dir = f"{artifacts_dir}/{graph_id}/{self.request.id}"
        os.makedirs(job_dir, exist_ok=True)
        
        result_file = f"{job_dir}/layout.json"
        with open(result_file, 'w') as f:
            json.dump([p.dict() for p in positions], f, indent=2)
        
        logger.info(f"Layout computation completed for {graph_id}")
        
        return {
            'graph_id': graph_id,
            'algorithm': algorithm,
            'num_nodes': len(positions),
            'artifacts': [result_file]
        }
    except Exception as e:
        logger.error(f"Layout computation failed: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True, name='run_centrality')
def run_centrality(self, graph_id: str, metrics: list, layers: list = None):
    """Compute centrality metrics"""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 10, 'phase': 'initializing'})
        
        # Compute centrality
        self.update_state(state='PROGRESS', meta={'progress': 30, 'phase': 'computing centrality'})
        results = compute_centrality(graph_id, metrics, layers)
        
        # Save results
        self.update_state(state='PROGRESS', meta={'progress': 80, 'phase': 'saving results'})
        artifacts_dir = get_artifacts_dir()
        job_dir = f"{artifacts_dir}/{graph_id}/{self.request.id}"
        os.makedirs(job_dir, exist_ok=True)
        
        result_file = f"{job_dir}/centrality.json"
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Centrality computation completed for {graph_id}")
        
        return {
            'graph_id': graph_id,
            'metrics': metrics,
            'results': results,
            'artifacts': [result_file]
        }
    except Exception as e:
        logger.error(f"Centrality computation failed: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True, name='run_community')
def run_community(self, graph_id: str, algorithm: str = "louvain",
                  resolution: float = 1.0, seed: int = 42):
    """Compute community detection"""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 10, 'phase': 'initializing'})
        
        # Compute communities
        self.update_state(state='PROGRESS', meta={'progress': 30, 'phase': 'detecting communities'})
        result = compute_community(graph_id, algorithm, resolution, seed)
        
        # Save results
        self.update_state(state='PROGRESS', meta={'progress': 80, 'phase': 'saving results'})
        artifacts_dir = get_artifacts_dir()
        job_dir = f"{artifacts_dir}/{graph_id}/{self.request.id}"
        os.makedirs(job_dir, exist_ok=True)
        
        result_file = f"{job_dir}/community.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Community detection completed for {graph_id}")
        
        return {
            'graph_id': graph_id,
            'algorithm': algorithm,
            'num_communities': result['num_communities'],
            'results': result,
            'artifacts': [result_file]
        }
    except Exception as e:
        logger.error(f"Community detection failed: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
