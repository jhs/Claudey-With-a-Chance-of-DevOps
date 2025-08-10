"""Visualization utilities for Chatfield LangGraph workflows."""

from typing import Optional, Dict, Any
from .socrates import SocratesMeta, process_socrates_class
from .agent import ChatfieldAgent
from langchain_openai import ChatOpenAI


def get_agent_graph(
    meta: SocratesMeta, 
    llm: Optional[ChatOpenAI] = None,
    max_retries: int = 3,
    temperature: float = 0.7
):
    """Create a ChatfieldAgent and return its compiled graph for visualization.
    
    Args:
        meta: SocratesMeta object containing field definitions
        llm: Optional LLM instance (defaults to ChatOpenAI)
        max_retries: Maximum validation retry attempts
        temperature: LLM temperature setting
        
    Returns:
        Compiled LangGraph that can be visualized
        
    Example:
        >>> from chatfield import get_agent_graph, Gatherer
        >>> 
        >>> class MyForm(Gatherer):
        >>>     name: "Your name"
        >>>     email: "Your email"
        >>> 
        >>> meta = process_socrates_class(MyForm)
        >>> graph = get_agent_graph(meta)
        >>> 
        >>> # In Jupyter notebook:
        >>> from IPython.display import Image, display
        >>> display(Image(graph.get_graph().draw_mermaid_png()))
    """
    agent = ChatfieldAgent(
        meta=meta,
        llm=llm,
        max_retries=max_retries,
        temperature=temperature
    )
    return agent.get_graph()


def get_graph_from_class(
    cls: type,
    llm: Optional[ChatOpenAI] = None,
    max_retries: int = 3,
    temperature: float = 0.7
):
    """Create a graph directly from a decorated Socrates class.
    
    Args:
        cls: A class inheriting from Gatherer
        llm: Optional LLM instance
        max_retries: Maximum validation retry attempts
        temperature: LLM temperature setting
        
    Returns:
        Compiled LangGraph for visualization
        
    Example:
        >>> from chatfield import get_graph_from_class, Gatherer
        >>> 
        >>> class SimpleForm(Gatherer):
        >>>     name: "Your name"
        >>> 
        >>> graph = get_graph_from_class(SimpleForm)
    """
    meta = process_socrates_class(cls)
    return get_agent_graph(meta, llm, max_retries, temperature)


def visualize_graph(graph, output_path: Optional[str] = None) -> Optional[bytes]:
    """Visualize a LangGraph as a Mermaid diagram.
    
    Args:
        graph: A compiled LangGraph
        output_path: Optional path to save the PNG image
        
    Returns:
        PNG image bytes if no output_path specified
        
    Example:
        >>> from chatfield import get_agent_graph, visualize_graph
        >>> graph = get_agent_graph(meta)
        >>> 
        >>> # Save to file
        >>> visualize_graph(graph, "workflow.png")
        >>> 
        >>> # Or get bytes for display
        >>> img_bytes = visualize_graph(graph)
        >>> from IPython.display import Image, display
        >>> display(Image(img_bytes))
    """
    try:
        # Get the Mermaid PNG representation
        png_bytes = graph.get_graph().draw_mermaid_png()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"Graph saved to {output_path}")
            return None
        else:
            return png_bytes
            
    except Exception as e:
        print(f"Error visualizing graph: {e}")
        print("Make sure you have the required dependencies installed:")
        print("  pip install grandalf")
        return None


def get_graph_metadata(graph) -> Dict[str, Any]:
    """Extract metadata about a LangGraph structure.
    
    Args:
        graph: A compiled LangGraph
        
    Returns:
        Dictionary with graph metadata including nodes, edges, etc.
        
    Example:
        >>> from chatfield import get_agent_graph, get_graph_metadata
        >>> graph = get_agent_graph(meta)
        >>> metadata = get_graph_metadata(graph)
        >>> print(f"Nodes: {metadata['nodes']}")
        >>> print(f"Edges: {metadata['edges']}")
    """
    try:
        graph_obj = graph.get_graph()
        
        # Extract nodes and edges
        nodes = list(graph_obj.nodes.keys()) if hasattr(graph_obj, 'nodes') else []
        edges = []
        
        if hasattr(graph_obj, 'edges'):
            for edge in graph_obj.edges:
                if hasattr(edge, 'source') and hasattr(edge, 'target'):
                    edges.append((edge.source, edge.target))
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
    except Exception as e:
        return {
            "error": str(e),
            "nodes": [],
            "edges": []
        }


def display_graph_in_notebook(graph):
    """Display a LangGraph visualization directly in a Jupyter notebook.
    
    Args:
        graph: A compiled LangGraph
        
    Example:
        >>> from chatfield import get_agent_graph, display_graph_in_notebook
        >>> graph = get_agent_graph(meta)
        >>> display_graph_in_notebook(graph)
    """
    try:
        from IPython.display import Image, display
        png_bytes = graph.get_graph().draw_mermaid_png()
        display(Image(png_bytes))
    except ImportError:
        print("IPython not available. This function requires Jupyter notebook environment.")
        print("Install with: pip install ipython jupyter")
    except Exception as e:
        print(f"Error displaying graph: {e}")