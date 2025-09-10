"""
Workflow processing utilities for CrewAI output parsing and transformation
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class WorkflowProcessor:
    """Handles parsing and transformation of CrewAI outputs to React Flow format"""
    
    @staticmethod
    def parse_crew_output(crew_output: Any, domain: str = "general") -> Optional[Dict[str, Any]]:
        """
        Parse CrewAI output to extract workflow JSON
        
        Args:
            crew_output: Raw output from CrewAI crew.kickoff()
            domain: Business domain for context
            
        Returns:
            Parsed workflow dict with nodes and edges, or None if parsing fails
        """
        logger.debug(f"CrewAI output type: {type(crew_output)}")
        logger.debug(f"CrewAI output attributes: {dir(crew_output) if hasattr(crew_output, '__dict__') else 'No attributes'}")
        
        # Handle different CrewAI output formats
        result_text = ""
        
        # If it's just a string, use it directly
        if isinstance(crew_output, str):
            result_text = crew_output
            logger.debug("CrewAI output is a string")
        else:
            # Try direct JSON extraction from CrewAI output object
            if hasattr(crew_output, 'json_dict') and crew_output.json_dict:
                try:
                    potential_json = crew_output.json_dict
                    if isinstance(potential_json, dict) and ('nodes' in potential_json or 'edges' in potential_json):
                        logger.info("Successfully parsed from json_dict")
                        return potential_json
                except Exception as e:
                    logger.debug(f"Failed to parse json_dict: {str(e)}")
            
            # Try to get raw text from different possible attributes
            if hasattr(crew_output, 'raw'):
                result_text = crew_output.raw
                logger.debug("Using crew_output.raw")
            elif hasattr(crew_output, 'result'):
                result_text = crew_output.result
                logger.debug("Using crew_output.result")
            elif hasattr(crew_output, 'output'):
                result_text = crew_output.output
                logger.debug("Using crew_output.output")
            else:
                result_text = str(crew_output)
                logger.debug("Converting crew_output to string")
            
            # Try task outputs if available
            if hasattr(crew_output, 'tasks_output') and crew_output.tasks_output:
                try:
                    # Get the last task (visualizer) output
                    last_task_output = crew_output.tasks_output[-1]
                    if hasattr(last_task_output, 'raw'):
                        result_text = last_task_output.raw
                        logger.debug("Using last task raw output")
                    elif hasattr(last_task_output, 'result'):
                        result_text = last_task_output.result
                        logger.debug("Using last task result")
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Could not access task outputs: {str(e)}")
        
        logger.debug(f"Final result_text length: {len(result_text)}")
        logger.debug(f"Result text preview: {result_text[:200]}...")
        
        # Extract JSON from text
        return WorkflowProcessor._extract_json_from_text(result_text)
    
    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON workflow from text using multiple patterns"""
        
        if not text:
            return None
        
        # First, try to parse the text directly as JSON
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            try:
                cleaned_json = WorkflowProcessor._clean_json_string(text)
                potential_json = json.loads(cleaned_json)
                if isinstance(potential_json, dict) and ('nodes' in potential_json or 'edges' in potential_json):
                    logger.info("Successfully parsed text as direct JSON")
                    return potential_json
            except json.JSONDecodeError as e:
                logger.debug(f"Direct JSON parsing failed: {str(e)}")
        
        # Try pattern-based extraction
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # Markdown JSON blocks
            r'```\s*([\s\S]*?)\s*```',      # Generic code blocks
            r'(\{[\s\S]*?"nodes"[\s\S]*?\})',  # JSON with nodes (capture group)
            r'(\{[\s\S]*?"edges"[\s\S]*?\})',  # JSON with edges (capture group)
            r'Final Answer[:\s]*([\s\S]*?)(?=\n\n|$)', # Final Answer format
        ]
        
        for i, pattern in enumerate(json_patterns):
            try:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                if matches:
                    logger.debug(f"Pattern {i+1} found {len(matches)} matches")
                    for match in matches:
                        try:
                            cleaned_json = WorkflowProcessor._clean_json_string(match)
                            potential_json = json.loads(cleaned_json)
                            
                            if isinstance(potential_json, dict) and ('nodes' in potential_json or 'edges' in potential_json):
                                logger.info(f"Successfully parsed with pattern {i+1}")
                                return potential_json
                        except json.JSONDecodeError as e:
                            logger.debug(f"JSON decode failed for pattern {i+1}: {str(e)}")
                            continue
            except Exception as e:
                logger.debug(f"Pattern {i+1} extraction failed: {str(e)}")
                continue
        
        return None
    
    @staticmethod
    def _clean_json_string(json_str: str) -> str:
        """Clean and fix common JSON formatting issues"""
        if not isinstance(json_str, str):
            return str(json_str)
        
        cleaned = json_str.strip()
        
        # Remove truncation indicators
        cleaned = cleaned.replace('...', '')
        
        # Fix common quote issues
        cleaned = cleaned.replace('responseNode"', '"responseNode"')
        
        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Simple fix for unquoted keys - be more careful to avoid over-replacement
        # Only fix keys that are clearly unquoted (alphanumeric followed by colon)
        cleaned = re.sub(r'(\n\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
        cleaned = re.sub(r'(\{\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
        cleaned = re.sub(r'(,\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
        
        # Fix double-quoted keys (remove extra quotes)
        cleaned = re.sub(r'"("[\w]+"):', r'\1:', cleaned)
        
        return cleaned
    
    @staticmethod
    def transform_to_react_flow(workflow_data: Dict[str, Any], domain: str = "general") -> Dict[str, Any]:
        """
        Transform workflow data to React Flow compatible format
        
        Args:
            workflow_data: Raw workflow data with nodes and edges
            domain: Business domain for enhanced descriptions
            
        Returns:
            React Flow compatible workflow dict
        """
        if not workflow_data or not isinstance(workflow_data, dict):
            logger.error("Invalid workflow_data provided to transform_to_react_flow")
            return {"nodes": [], "edges": []}
        
        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])
        
        # Ensure nodes and edges are lists
        if not isinstance(nodes, list):
            logger.error(f"nodes is not a list: {type(nodes)}")
            nodes = []
        if not isinstance(edges, list):
            logger.error(f"edges is not a list: {type(edges)}")
            edges = []
        
        # Transform nodes
        transformed_nodes = []
        for i, node in enumerate(nodes):
            transformed_node = WorkflowProcessor._transform_node(node, i, domain)
            transformed_nodes.append(transformed_node)
        
        # Transform edges
        transformed_edges = []
        for i, edge in enumerate(edges):
            transformed_edge = WorkflowProcessor._transform_edge(edge, i)
            if transformed_edge:
                transformed_edges.append(transformed_edge)
        
        return {
            'nodes': transformed_nodes,
            'edges': transformed_edges
        }
    
    @staticmethod
    def _transform_node(node: Dict[str, Any], index: int, domain: str) -> Dict[str, Any]:
        """Transform a single node to React Flow format"""
        
        # Handle non-dict nodes by creating a fallback dict
        if not isinstance(node, dict):
            logger.warning(f"Transform received non-dict node: {type(node)} - {node}")
            node = {
                'id': f'fallback_{index}',
                'label': str(node) if node else f'Step {index + 1}',
                'type': 'action'
            }
        
        node_id = node.get('id', f'node_{index}')
        node_type = node.get('type', node.get('nodeType', 'action'))
        node_label = node.get('label', node.get('name', f'Step {index + 1}'))
        
        # Professional icon mapping
        icon_map = {
            'webhook': '🔗', 'http': '🌐', 'database': '💾', 
            'email': '📧', 'code': '💻', 'validation': '✅',
            'approval': '👥', 'notification': '🔔', 'security': '🔐',
            'analytics': '📊', 'audit': '📋', 'monitoring': '👁️',
            'encryption': '🔒', 'compliance': '🛡️', 'alert': '⚠️'
        }
        
        # Domain-specific icon enhancements
        if domain == "healthcare" and 'patient' in node_label.lower():
            icon_map.update({'http': '👤', 'validation': '🏥'})
        elif domain == "finance" and 'fraud' in node_label.lower():
            icon_map.update({'validation': '🚨', 'monitoring': '🔍'})
        
        # Build node data
        if 'data' not in node:
            node_data = {
                'label': node_label,
                'nodeType': node_type,
                'icon': icon_map.get(node_type, '⚙️'),
                'description': node.get('description', f'Automated {node_type} step'),
                'locked': 'compliance' in node_label.lower() or 'audit' in node_label.lower(),
                'compliance_reason': 'Required for regulatory compliance' if 'compliance' in node_label.lower() else None
            }
        else:
            node_data = node['data']
        
        # Ensure position exists
        if 'position' not in node:
            node['position'] = {'x': 100 + (index % 4) * 200, 'y': 100 + (index // 4) * 150}
        
        return {
            'id': node_id,
            'type': 'n8nNode',
            'position': node['position'],
            'data': node_data
        }
    
    @staticmethod
    def _transform_edge(edge: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Transform a single edge to React Flow format"""
        
        # Handle non-dict edges
        if not isinstance(edge, dict):
            logger.warning(f"Transform received non-dict edge: {type(edge)} - {edge}")
            return None
        
        edge_id = edge.get('id', f'edge_{index}')
        
        # Handle from/to to source/target transformation
        if 'from' in edge and 'to' in edge:
            source = edge['from']
            target = edge['to']
            # Handle array values (take first)
            if isinstance(source, list):
                source = source[0] if source else None
            if isinstance(target, list):
                target = target[0] if target else None
        else:
            source = edge.get('source')
            target = edge.get('target')
        
        if not source or not target:
            return None
        
        return {
            'id': edge_id,
            'source': source,
            'target': target
        }
    
    @staticmethod
    def filter_domain_compliance(nodes: List[Dict], edges: List[Dict], domain: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter nodes and edges based on domain compliance
        
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            domain: Business domain
            
        Returns:
            Tuple of (filtered_nodes, filtered_edges)
        """
        DOMAIN_COMPLIANCE = {
            'healthcare': {
                'allowed': ['hipaa', 'patient', 'medical', 'clinical', 'phi', 'healthcare', 'consent'],
                'forbidden': ['kyc', 'aml', 'sox', 'pci', 'banking', 'financial', 'fraud_detection']
            },
            'finance': {
                'allowed': ['kyc', 'aml', 'sox', 'pci', 'banking', 'financial', 'fraud', 'transaction'],
                'forbidden': ['hipaa', 'patient', 'medical', 'clinical', 'phi', 'healthcare']
            },
            'creator': {
                'allowed': ['dmca', 'copyright', 'content', 'moderation', 'coppa', 'creator'],
                'forbidden': ['hipaa', 'patient', 'medical', 'kyc', 'aml', 'sox', 'pci']
            }
        }
        
        if domain not in DOMAIN_COMPLIANCE:
            return nodes, edges
        
        domain_rules = DOMAIN_COMPLIANCE[domain]
        filtered_nodes = []
        removed_node_ids = set()
        
        for node in nodes:
            # Ensure node is a dict before processing
            if not isinstance(node, dict):
                logger.warning(f"Skipping non-dict node: {type(node)} - {node}")
                continue
                
            node_text = WorkflowProcessor._get_node_text(node).lower()
            
            # Check if node contains forbidden terms
            has_forbidden = any(term in node_text for term in domain_rules['forbidden'])
            
            if has_forbidden:
                node_id = node.get('id', 'unknown')
                removed_node_ids.add(node_id)
                logger.info(f"Filtered out node '{node_id}' - contains {domain} forbidden terms")
            else:
                filtered_nodes.append(node)
        
        # Filter edges that reference removed nodes
        filtered_edges = []
        for edge in edges:
            # Ensure edge is a dict before processing
            if not isinstance(edge, dict):
                logger.warning(f"Skipping non-dict edge: {type(edge)} - {edge}")
                continue
                
            source = edge.get('source', '')
            target = edge.get('target', '')
            
            if source not in removed_node_ids and target not in removed_node_ids:
                filtered_edges.append(edge)
        
        return filtered_nodes, filtered_edges
    
    @staticmethod
    def _get_node_text(node: Dict[str, Any]) -> str:
        """Extract all text from a node for compliance checking"""
        if not isinstance(node, dict):
            return str(node) if node else ''
            
        texts = []
        texts.append(node.get('label', ''))
        texts.append(node.get('description', ''))
        
        if 'data' in node and isinstance(node['data'], dict):
            data = node['data']
            texts.append(data.get('label', ''))
            texts.append(data.get('description', ''))
        
        return ' '.join(str(t) for t in texts if t)
    
    @staticmethod
    def validate_react_flow_format(workflow_data: Dict[str, Any]) -> bool:
        """Validate that workflow data matches React Flow expected format"""
        try:
            if 'nodes' in workflow_data:
                for node in workflow_data['nodes']:
                    if not all(key in node for key in ['id', 'type', 'position']):
                        return False
                    if 'data' not in node:
                        return False
            
            if 'edges' in workflow_data:
                for edge in workflow_data['edges']:
                    if not all(key in edge for key in ['id', 'source', 'target']):
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False